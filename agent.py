"""
nghiên cứu thêm streaming + logging + PRESERVE THINKING.

persistent memory + context bloating

ngắt quảng khi gọi tools liên tiếp cách giả quyết. 
"""

import json
import os

from dotenv import load_dotenv
from litellm import completion

from memory import (
    THRESHOLD,
    append_turn,
    archive_session,
    compact_context,
    count_tokens,
    load_context,
    session_exists,
)
from prompt import (
    SYSTEM_PROMPT,
    TOOL_DECLARATION,
)
from tools.shell import run_shell

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_BASE = os.getenv("API_BASE")
MODEL = os.getenv("MODEL")


def brief_args(name, args):
    """Rút gọn args để in log cho gọn"""
    if name == "run_terminal":
        cmd = args.get("command", "").strip()

        # 1. Nếu là lệnh tạo/ghi file bằng Heredoc (cat << 'EOF' > filename)
        if "cat <<" in cmd and ">" in cmd:
            lines = cmd.splitlines()
            first_line = lines[0]  # Dòng đầu: cat << 'EOF' > src/main.py

            target_file = (
                first_line.split(">")[-1].strip().replace("'", "").replace('"', "")
            )
            line_count = len(lines) - 2
            return f"[Create File] {target_file} ({line_count} lines)"

        # 2. Nếu là lệnh Terminal đơn dòng thông thường (python, git, ls, mkdir...)
        clean_cmd = " ".join(cmd.split())

        if len(clean_cmd) > 65:
            return f" {clean_cmd[:62]}..."
        return f"{clean_cmd}"
    else:
        return str(args)[:50]


def save_message(context: list[dict], msg: dict) -> None:
    """Vừa chèn context vừa append vào file, Chọn JSONL để giữ tốc độ"""
    context.append(msg)
    entry = {"type": "msg", **msg}
    append_turn(entry)


TOOLS = {
    "run_terminal": {
        "type": "cli",
        "handler": run_shell,
    },
}


def execute_tool(name: str, args: dict):
    tool = TOOLS.get(name, None)
    if not tool or "handler" not in tool:
        return {"success": False, "error": f"KHONG CO TOOL: {name}"}
    return tool["handler"](**args)


def agents_loop(context: list[dict]):
    loop_count = 0
    while True:

        token_count = count_tokens(context)
        if token_count > THRESHOLD:
            print(f"\n Context vượt ngưỡng ({token_count} > {THRESHOLD} tokens)")
            context = compact_context(
                context,
                API_KEY,
                API_BASE,
                MODEL,
            )
            new_count = count_tokens(context)
            print(f"Compact xong: {new_count} tokens\n")

        response = completion(
            model=MODEL,
            messages=context,
            api_key=API_KEY,
            api_base=API_BASE,
            tools=TOOL_DECLARATION,
            timeout=120,
            stream=True,
        )
        loop_count += 1

        full_text = ""
        full_reasoning = ""
        tool_call_buffers = {}

        for chunk in response:
            delta = chunk.choices[0].delta

            if getattr(delta, "reasoning_content", None):
                # reasoning trước khi chọn tool, đưa ngược lại vào model.
                print(f"\033[90m{delta.reasoning_content}\033[0m", end="", flush=True)
                full_reasoning += delta.reasoning_content

            if delta.content:
                # suy nghix sau khi nhận được kết quả.
                print(delta.content, end="", flush=True)
                full_text += delta.content

            # bắt mảnh
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_call_buffers:
                        tool_call_buffers[idx] = {
                            "id": "",
                            "name": "",
                            "arguments": "",
                        }
                    buf = tool_call_buffers[idx]

                    if tc.id:
                        buf["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            buf["name"] += tc.function.name
                        if tc.function.arguments:
                            buf["arguments"] += tc.function.arguments

        # buffer không rỗng nghĩa là muốn gọi tool
        if tool_call_buffers:
            tool_calls = []
            for idx in sorted(tool_call_buffers.keys()):
                buf = tool_call_buffers[idx]
                tool_calls.append(
                    {
                        "id": buf["id"],
                        "type": "function",
                        "function": {
                            "name": buf["name"],
                            "arguments": buf["arguments"],
                        },
                    }
                )

            save_message(
                context,
                {
                    "role": "assistant",
                    "reasoning_content": full_reasoning or None,
                    "content": full_text or None,
                    "tool_calls": tool_calls,
                },
            )
            # print(f"[DEBUGGING] {len(tool_calls)}")
            for tc in tool_calls:
                name = tc["function"]["name"]
                args = json.loads(tc["function"]["arguments"])

                try:
                    result = execute_tool(name, args)
                    brief = brief_args(name, args)
                    status = "TRUE" if result.get("success") else "FALSE"
                    err_msg = result.get("error") or result.get("stderr", "").strip()
                    print(
                        f"\n[Loop {loop_count}] {name}({brief}) {status}"
                        + (
                            f" -> Lỗi: {err_msg[:80]}"
                            if not result.get("success")
                            else ""
                        )
                    )
                except Exception as e:
                    result = {"success": False, "error": str(e)}

                save_message(
                    context,
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": name,
                        "content": json.dumps(result),
                    },
                )
            print()
        else:
            print()
            save_message(
                context,
                {
                    "role": "assistant",
                    "reasoning_content": full_reasoning or None,
                    "content": full_text or None,
                },
            )
            return full_text


if __name__ == "__main__":
    if session_exists():
        ans = input("Có session cũ. Resume? (y/n): ").strip().lower()
        if ans == "y":
            context = load_context()
            print(f"Resume session: {len(context)} messages")
        else:
            archive_session()
            context = [{"role": "system", "content": SYSTEM_PROMPT}]
            append_turn({"type": "msg", "role": "system", "content": SYSTEM_PROMPT})
            print("Session mới đã được tạo.\n")
    else:
        context = [{"role": "system", "content": SYSTEM_PROMPT}]
        append_turn({"type": "msg", "role": "system", "content": SYSTEM_PROMPT})

    # append_turn(context)
    while True:

        try:
            prompt = input("Bạn: ").strip()

        except (EOFError, KeyboardInterrupt):
            # Ctrl+C hoặc Ctrl+D
            print(
                f"\n Context đã lưu ({len(context)} messages). Tạm biệt master Nguyen!"
            )
            break

        if prompt.lower() in {"exit", ""}:
            # exit bình thường
            print(
                f" Context đã lưu ({len(context)} messages). Tạm biệt master Nguyen!"
            )
            break

        save_message(context, {"role": "user", "content": prompt})

        try:
            agents_loop(context)
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
