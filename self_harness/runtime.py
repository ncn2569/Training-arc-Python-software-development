"""The compact agent runtime used only inside self_harness workspaces.

It runs a conventional ReAct loop with the root tool contract, records every
turn, and prints a compact live trace without modifying the root agent code.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import time
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps, UnidentifiedImageError

from .config import PROJECT_ROOT, SAFETY_PREFIX
from .models import ProviderCallError, call_model


MAX_TEXT_CHARS = 50_000
MAX_PROVIDER_TURN_ATTEMPTS = 3
PROVIDER_TURN_RETRY_DELAY_SECONDS = 2
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MIME_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}


def _workspace_path(workspace: Path, raw_path: str) -> Path:
    """Resolve an agent path and enforce the per-task workspace boundary."""
    requested = Path(raw_path)
    if requested.parts and requested.parts[0].lower() in {"workspace", ".workspace"}:
        requested = Path(*requested.parts[1:])
    result = (workspace / requested).resolve()
    if not result.is_relative_to(workspace.resolve()):
        raise ValueError("Path must stay inside the task workspace")
    return result


def _read_file(workspace: Path, path: str, range: list[int] | None = None, limit: int | None = None) -> dict[str, Any]:
    """Return bounded UTF-8 text or a normalized image payload for one file."""
    file_path = _workspace_path(workspace, path)
    if not file_path.exists() or not file_path.is_file():
        return {"success": False, "path": path, "error": "FILE NOT FOUND"}
    suffix = file_path.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        try:
            with Image.open(file_path) as source:
                image = ImageOps.exif_transpose(source) or source
                width, height = image.size
                if suffix in {".jpg", ".jpeg"} and image.mode not in {"RGB", "L"}:
                    image = image.convert("RGB")
                output = BytesIO()
                image.save(output, format="JPEG" if suffix in {".jpg", ".jpeg"} else suffix[1:].upper())
            return {
                "success": True,
                "type": "image",
                "path": path,
                "mime_type": MIME_TYPES[suffix],
                "image_width": width,
                "image_height": height,
                "size_bytes": file_path.stat().st_size,
                "data_url": f"data:{MIME_TYPES[suffix]};base64,{base64.b64encode(output.getvalue()).decode('ascii')}",
            }
        except (OSError, UnidentifiedImageError) as exc:
            return {"success": False, "path": path, "error": str(exc)}
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return {"success": False, "path": path, "error": "File is not UTF-8 text or a supported image"}
    start = 1
    if range is not None:
        if len(range) != 2 or range[0] < 1:
            return {"success": False, "path": path, "error": "range must be [start_line, end_line]"}
        start, end = range
        lines = lines[start - 1 : end]
    if limit and limit > 0:
        lines = lines[:limit]
    content = "\n".join(f"{number}: {line}" for number, line in enumerate(lines, start=start))
    truncated = len(content) > MAX_TEXT_CHARS
    if truncated:
        content = content[:MAX_TEXT_CHARS]
    return {
        "success": True,
        "path": path,
        "total_lines": len(file_path.read_text(encoding="utf-8").splitlines()),
        "truncated": truncated,
        "content": content,
    }


def _write_file(workspace: Path, path: str, content: str) -> dict[str, Any]:
    """Create or replace a UTF-8 workspace file, creating parent directories."""
    target = _workspace_path(workspace, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    action = "OVERWRITE" if target.exists() else "CREATE"
    target.write_text(content, encoding="utf-8")
    return {"success": True, "path": path, "action": action, "bytes_written": len(content.encode("utf-8"))}


def _replace_file(workspace: Path, path: str, old_string: str, new_string: str, replace_all: bool = False) -> dict[str, Any]:
    """Perform a guarded exact replacement; ambiguous edits require opt-in."""
    target = _workspace_path(workspace, path)
    if not target.exists():
        return {"success": False, "path": path, "error": "FILE NOT FOUND"}
    content = target.read_text(encoding="utf-8")
    occurrences = content.count(old_string)
    if occurrences == 0:
        return {"success": False, "path": path, "error": "old string not found"}
    if occurrences > 1 and not replace_all:
        return {"success": False, "path": path, "error": "AMBIGUOUS MATCH; make old_string more specific"}
    target.write_text(content.replace(old_string, new_string), encoding="utf-8")
    return {"success": True, "path": path, "occurrences_replaced": occurrences if replace_all else 1}


def _run_terminal(workspace: Path, command: str) -> dict[str, Any]:
    """Run one bounded non-interactive shell command in the task workspace."""
    forbidden = ("rm -rf /", "rm -rf ~", "shutdown", "reboot", "format ", "stop-computer")
    if any(item in command.lower() for item in forbidden):
        return {"success": False, "error": "Blocked unsafe command"}
    bash_path = os.getenv("BASH_PATH", r"D:\git\Git\bin\bash.exe")
    try:
        result = subprocess.run(
            [bash_path, "-c", command],
            cwd=workspace,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            env=os.environ.copy(),
        )
        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout[-MAX_TEXT_CHARS:],
            "stderr": result.stderr[-MAX_TEXT_CHARS:],
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "COMMAND_TIMEOUT"}
    except OSError as exc:
        return {"success": False, "error": str(exc)}


def _grep(workspace: Path, pattern: str, path: str, glob: str | None = None, output_mode: str = "files_with_matches", context: int | None = None) -> dict[str, Any]:
    """Search only under the workspace and return a bounded structured result."""
    target = _workspace_path(workspace, path)
    command = ["grep", "--color=never", "-n", "-r", "-H"]
    if output_mode == "files_with_matches":
        command.append("-l")
    elif output_mode == "count":
        command.append("-c")
    elif context is not None:
        command.extend(["-C", str(context)])
    if glob:
        command.append(f"--include={glob}")
    command.extend([pattern, str(target).replace("\\", "/")])
    result = subprocess.run(command, cwd=workspace, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode not in {0, 1}:
        return {"success": False, "error": result.stderr.strip() or "grep failed"}
    lines = result.stdout.splitlines()
    return {"success": True, "pattern": pattern, "path": path, "output_mode": output_mode, "matches": lines[:500], "total_matches": len(lines)}


def _load_skill(name: str) -> dict[str, Any]:
    """Delegate skill lookup to the root agent's existing skill loader."""
    import sys

    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from agent_skills.loader import load_skill

    return load_skill(name)


def execute_tool(name: str, args: dict[str, Any], workspace: Path) -> dict[str, Any]:
    """Dispatch the immutable harness tool contract and normalize tool failures."""
    try:
        match name:
            case "read_file":
                return _read_file(workspace, **args)
            case "write_file":
                return _write_file(workspace, **args)
            case "str_replace_editor":
                return _replace_file(workspace, **args)
            case "run_terminal":
                return _run_terminal(workspace, **args)
            case "grep_search":
                return _grep(workspace, **args)
            case "load_skill":
                return _load_skill(**args)
            case _:
                return {"success": False, "error": f"Unknown tool: {name}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def _tool_payload(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("type") != "image":
        return result
    return {key: value for key, value in result.items() if key != "data_url"}


def _tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    calls = message.get("tool_calls") or []
    return [call for call in calls if isinstance(call, dict) and isinstance(call.get("function"), dict)]


def _short(value: Any, limit: int = 150) -> str:
    """Make live terminal output readable while retaining full data in JSON."""
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else f"{text[:limit - 1]}…"


def _provider_reasoning(message: dict[str, Any]) -> str:
    """Extract provider-exposed reasoning once for the durable trajectory log.

    Different gateways place this public field at ``reasoning_content``,
    ``reasoning``, or inside ``provider_specific_fields``. This function does
    not ask the model for hidden reasoning; it records only text the provider
    already returned in its response. It is retained in full so the judge and
    tuner can inspect the complete provider-exposed trajectory.
    """
    values: list[Any] = [message.get("reasoning_content"), message.get("reasoning")]
    provider_fields = message.get("provider_specific_fields")
    if isinstance(provider_fields, dict):
        values.extend([provider_fields.get("reasoning"), provider_fields.get("reasoning_content")])
        details = provider_fields.get("reasoning_details")
        if isinstance(details, list):
            values.extend(item.get("text") for item in details if isinstance(item, dict))
    for value in values:
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _trajectory_message(message: dict[str, Any]) -> dict[str, Any]:
    """Keep normal assistant output while moving provider reasoning to one field."""
    excluded = {"reasoning", "reasoning_content", "provider_specific_fields"}
    return {key: value for key, value in message.items() if key not in excluded}


def _print_turn(label: str, turn: int, max_turns: int, model: str, usage: dict[str, Any], call_time: float, message: dict[str, Any], calls: list[dict[str, Any]]) -> None:
    print(f"\n╭─ {label} · turn {turn}/{max_turns} {'─' * 32}")
    print(f"│ model {model} · {call_time:.2f}s · {usage['total_tokens']:,} tokens (in {usage['input_tokens']:,}, out {usage['output_tokens']:,}; {usage['source']})")
    text = _short(message.get("content") or message.get("reasoning_content"))
    if text:
        print(f"│ assistant: {text}")
    if calls:
        print(f"│ tool calls: {len(calls)}")


def _print_tool(name: str, args: dict[str, Any], result: dict[str, Any]) -> None:
    marker = "✓" if result.get("success") else "✗"
    detail = result.get("error") or result.get("stderr") or result.get("action") or "ok"
    path = args.get("path") or args.get("file_path") or ""
    suffix = f" · {path}" if path else ""
    print(f"│ {marker} {name}{suffix}: {_short(detail, 120)}")


def run_agent(
    *,
    settings: dict[str, str],
    config: dict[str, Any],
    task_prompt: str,
    workspace: Path,
    max_turns: int,
    timeout_seconds: int,
    label: str = "agent",
) -> dict[str, Any]:
    """Run the compact ReAct loop and capture the complete durable trajectory.

    The loop has four phases per turn: check the fair time budget, obtain one
    model response with same-turn provider recovery, record the assistant
    response, then execute and feed back every requested tool result. Failed
    provider latency is excluded from ``wall_time`` but retained in metrics.
    """
    started = time.perf_counter()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": f"{SAFETY_PREFIX}\n{config['system_prompt']}"},
        {"role": "user", "content": task_prompt},
    ]
    trajectory: list[dict[str, Any]] = []
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "api_retries": 0,
        "provider_retry_cycles": 0,
        "provider_failure_seconds": 0.0,
        "tool_calls": 0,
        "tool_errors": 0,
        "tool_retries": 0,
    }
    provider_failure_time = 0.0
    failed_signatures: set[str] = set()
    final_answer = ""
    status = "max_turns"

    print(f"\n▶ {label} workspace: {workspace}")

    def measured_elapsed() -> float:
        return max(0.0, time.perf_counter() - started - provider_failure_time)

    for turn in range(1, max_turns + 1):
        # Phase 1: only successful agent work consumes the reward time budget.
        if measured_elapsed() > timeout_seconds:
            status = "timeout"
            break
        # Phase 2: retry a failed provider request in place. ``messages`` and
        # the workspace are intentionally untouched, so task progress survives.
        response: dict[str, Any] | None = None
        for retry_cycle in range(1, MAX_PROVIDER_TURN_ATTEMPTS + 1):
            try:
                response = call_model(
                    settings=settings, messages=messages, tools=config["tools"]
                )
                failed_seconds = float(response.get("provider_failure_time", 0.0))
                provider_failure_time += failed_seconds
                totals["provider_failure_seconds"] += failed_seconds
                if response["api_retries"]:
                    trajectory.append(
                        {
                            "turn": turn,
                            "kind": "provider_retry",
                            "cycle": retry_cycle,
                            "failed_requests": int(response["api_retries"]),
                            "failure_seconds": failed_seconds,
                            "recovered": True,
                        }
                    )
                break
            except ProviderCallError as exc:
                provider_failure_time += exc.failure_wall_time
                totals["provider_failure_seconds"] += exc.failure_wall_time
                totals["provider_retry_cycles"] += 1
                trajectory.append(
                    {
                        "turn": turn,
                        "kind": "provider_retry",
                        "cycle": retry_cycle,
                        "failed_requests": len(exc.errors),
                        "failure_seconds": exc.failure_wall_time,
                        "recovered": False,
                    }
                )
                print(f"\n│ provider unavailable on turn {turn}; retrying same turn ({retry_cycle}/{MAX_PROVIDER_TURN_ATTEMPTS})")
                if retry_cycle == MAX_PROVIDER_TURN_ATTEMPTS:
                    status = "model_error"
                    trajectory.append({"turn": turn, "kind": "model_error", "error": str(exc)})
                    print(f"│ ✗ provider retries exhausted: {_short(exc, 180)}")
                    break
                backoff_started = time.perf_counter()
                time.sleep(PROVIDER_TURN_RETRY_DELAY_SECONDS)
                retry_delay = time.perf_counter() - backoff_started
                provider_failure_time += retry_delay
                totals["provider_failure_seconds"] += retry_delay
            except Exception as exc:
                status = "model_error"
                trajectory.append({"turn": turn, "kind": "model_error", "error": str(exc)})
                print(f"\n╭─ {label} · turn {turn}/{max_turns} {'─' * 32}")
                print(f"│ ✗ model error: {_short(exc, 180)}")
                break
        if response is None:
            break
        # Phase 3: persist the provider-visible assistant event before tools.
        usage = response["usage"]
        for key in ("input_tokens", "output_tokens", "total_tokens"):
            totals[key] += int(usage[key])
        totals["api_retries"] += int(response["api_retries"])
        message = response["message"]
        calls = _tool_calls(message)
        _print_turn(label, turn, max_turns, response["model"], usage, response["wall_time"], message, calls)
        reasoning = _provider_reasoning(message)
        assistant_event = {
            "turn": turn,
            "kind": "assistant",
            "model": response["model"],
            "message": _trajectory_message(message),
            "usage": usage,
            "wall_time": response["wall_time"],
        }
        if reasoning:
            assistant_event["reasoning"] = reasoning
        trajectory.append(assistant_event)
        assistant_message: dict[str, Any] = {"role": "assistant", "content": message.get("content")}
        if calls:
            assistant_message["tool_calls"] = calls
        messages.append(assistant_message)
        if not calls:
            final_answer = str(message.get("content") or "")
            status = "completed"
            break

        # Phase 4: execute every tool call, then append matching tool messages
        # in call order. This preserves the model's tool-call protocol.
        tool_results: list[tuple[dict[str, Any], str, dict[str, Any]]] = []
        for call in calls:
            name = str(call["function"].get("name") or "")
            raw_args = str(call["function"].get("arguments") or "{}")
            try:
                args = json.loads(raw_args)
                if not isinstance(args, dict):
                    raise ValueError("Tool arguments must be an object")
            except Exception as exc:
                args = {}
                result = {"success": False, "error": f"Invalid tool JSON: {exc}"}
            else:
                signature = f"{name}:{json.dumps(args, sort_keys=True, ensure_ascii=False)}"
                if signature in failed_signatures:
                    totals["tool_retries"] += 1
                result = execute_tool(name, args, workspace)
                if not result.get("success"):
                    failed_signatures.add(signature)
            totals["tool_calls"] += 1
            if not result.get("success"):
                totals["tool_errors"] += 1
            tool_results.append((call, name, result))
            trajectory.append({"turn": turn, "kind": "tool", "name": name, "arguments": args, "result": _tool_payload(result)})
            _print_tool(name, args, result)

        for call, name, result in tool_results:
            messages.append({
                "role": "tool",
                "tool_call_id": call.get("id", ""),
                "name": name,
                "content": json.dumps(_tool_payload(result), ensure_ascii=False),
            })
        for _, name, result in tool_results:
            if result.get("type") == "image" and result.get("data_url"):
                messages.append({"role": "user", "content": [
                    {"type": "text", "text": f"[IMAGE CONTENT] from {name}"},
                    {"type": "image_url", "image_url": {"url": result["data_url"]}},
                ]})

    total_wall_time = measured_elapsed()
    print(f"╰─ {label} finished: {status} · {totals['total_tokens']:,} tokens · {len([entry for entry in trajectory if entry.get('kind') == 'assistant'])} turns · {total_wall_time:.2f}s")
    return {
        "status": status,
        "final_answer": final_answer,
        "turns": len([entry for entry in trajectory if entry.get("kind") == "assistant"]),
        "wall_time": total_wall_time,
        "metrics": totals,
        "trajectory": trajectory,
    }


def prepare_workspace(seed_dir: Path, destination: Path) -> None:
    """Replace one rollout workspace with an exact copy of its immutable seed."""
    if destination.exists():
        shutil.rmtree(destination)
    if seed_dir.exists():
        shutil.copytree(seed_dir, destination)
    else:
        destination.mkdir(parents=True)
