"""Create a compact, decision-focused view of an agent trajectory.

Raw trajectories remain complete in suite manifests for local audit. Judge and
tuner receive this narrower view so they can inspect reasoning and actions
without receiving full written source files or verbose tool payloads.
"""

from __future__ import annotations

import json
from typing import Any


def _reasoning(event: dict[str, Any]) -> str:
    """Read normalized reasoning or the equivalent field from older trajectories."""
    value = event.get("reasoning")
    if isinstance(value, str):
        return value
    message = event.get("message")
    if not isinstance(message, dict):
        return ""
    for candidate in (message.get("reasoning_content"), message.get("reasoning")):
        if isinstance(candidate, str):
            return candidate
    fields = message.get("provider_specific_fields")
    return str(fields.get("reasoning") or "") if isinstance(fields, dict) else ""


def _tool_intent(arguments: Any) -> dict[str, Any]:
    """Preserve actionable arguments while replacing source-body payloads."""
    if not isinstance(arguments, dict):
        return {"raw": str(arguments)}
    result: dict[str, Any] = {}
    for key, value in arguments.items():
        if key in {"content", "old_string", "new_string"} and isinstance(value, str):
            result[key] = f"<{len(value)} characters omitted>"
        else:
            result[key] = value
    return result


def _call_intent(call: dict[str, Any]) -> dict[str, Any]:
    """Convert a native assistant tool call into name plus compact arguments."""
    function = call.get("function", {}) if isinstance(call, dict) else {}
    raw = function.get("arguments", "{}") if isinstance(function, dict) else "{}"
    try:
        arguments = json.loads(str(raw))
    except json.JSONDecodeError:
        arguments = {"raw": str(raw)}
    return {
        "name": function.get("name") if isinstance(function, dict) else None,
        "arguments": _tool_intent(arguments),
    }


def review_trajectory(events: list[dict[str, Any]], *, factual_only: bool = False) -> list[dict[str, Any]]:
    """Return reasoning/text/tool/result evidence suitable for judge and tuner.

    Tuner events retain provider-exposed reasoning and visible text output.
    factual_only omits assistant/model/usage information for the judge. Tool
    events include IO metadata, exit status and bounded output tails. Source
    bodies and image payloads remain in local audit logs only.
    """
    view: list[dict[str, Any]] = []
    for event in events:
        kind = event.get("kind")
        if kind == "assistant":
            if factual_only:
                continue
            message = event.get("message") if isinstance(event.get("message"), dict) else {}
            calls = message.get("tool_calls") or []
            view.append({
                "turn": event.get("turn"),
                "kind": "assistant",
                "model": event.get("model"),
                "reasoning": _reasoning(event),
                "text_output": str(message.get("content") or ""),
                "tools": [_call_intent(call) for call in calls if isinstance(call, dict)],
                "usage": event.get("usage", {}),
            })
        elif kind == "tool":
            result = event.get("result")
            worked = bool(result.get("success")) if isinstance(result, dict) else False
            evidence = {"worked": worked}
            if isinstance(result, dict):
                for key in ("exit_code", "path", "type", "action", "bytes_written",
                            "image_width", "image_height", "size_bytes", "truncated", "error"):
                    if key in result:
                        evidence[key] = result[key]
                # Exit code/output is an observation, not proof of correctness.
                for key in ("stdout", "stderr"):
                    if result.get(key):
                        evidence[key] = str(result[key])[-1500:]
            view.append({
                "turn": event.get("turn"),
                "kind": "tool",
                "tool": event.get("name"),
                "arguments": _tool_intent(event.get("arguments", {})),
                "tool_result": evidence,
            })
        elif kind == "model_error":
            view.append({"turn": event.get("turn"), "kind": kind, "model_error": True})
        else:
            view.append({"turn": event.get("turn"), "kind": str(kind or "unknown")})
    return view
