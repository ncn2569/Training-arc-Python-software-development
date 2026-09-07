"""
refactor + system prompt + logging + file path.

nghiên cứu thêm streaming + logging + PRESERVE THINKING.

persistent memory + context bloating

ngắt quảng khi gọi tools liên tiếp cách giả quyết.

Đọc file siêu lớn nhưng vẫn giữ được context, nghiên cứu tách process terminal.

Đọc ảnh, từ sql diagram chuyển thành DML


WORKS rồi, nhưng còn vài vấn đề: 
    context length, đang trick lỏ bằng cái context 1m :  
    message list, hiện tại đang là 3 context cho mỗi lần: tool-result + content(user + image) -- Cline
    review cách người ta hiện thực hàm render
    output trả về, nên trả về text không hay cả ảnh và nên trả về những gì
    format ảnh, ảnh gen ra đang bị lệch.
    tư duy thiết kế tools, tools này đã là tools chưa hay là đang là function wrapper
    kiếm 1 cách trực quan hơn để theo dõi thông tin, hiện tại đang hơi rối.
    ....

Docker - uv package manager python - linux - .env  - Bun


Done (- remote ssh - VM)

READ FILE vạn năng tùy vào đuôi của file. -> READ IMAGE nếu đuôi là html + READ FILE nếu không phải.
start line end line optional nếu trường hợp muốn đọc code của 1 file html. 




Tạo benchmark: RL + LLM 
task : wall time : success rate 

"""

import json
import os
import sys
from pathlib import Path

# Thêm src/ vào sys.path để import được các package con
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from litellm import completion

from agent_skills.loader import load_skill as _load_skill
from context.memory import (
    THRESHOLD,
    append_turn,
    compact_context,
    count_tokens,
)
from context.prompt import (
    get_system_prompt,
    get_tool_declaration,
)
from tools.edit import str_replace_editor
from tools.grep import grep_search
# from tools.image import read_image
# from tools.image_2 import read_image_2
from tools.read import read_file

# from tools.render import render_file
from tools.shell import run_shell
from tools.write import write_file

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_BASE = os.getenv("API_BASE")
MODEL = os.getenv("MODEL")
TOOL_DECLARATION = get_tool_declaration()
SYSTEM_PROMPT = get_system_prompt()

TOOLS = {
    "run_terminal": {
        "handler": run_shell,
    },
    "read_file": {
        "handler": read_file,
    },
    "str_replace_editor": {
        "handler": str_replace_editor,
    },
    "write_file": {
        "handler": write_file,
    },
    "grep_search": {"handler": grep_search},
    "load_skill": {"handler": _load_skill},
    # "read_image": {"handler": read_image},
    # "read_image_2": {"handler": read_image_2},

    # "render_file": {
    #     "handler": render_file
    # }
}


def brief_args(name, args):
    """Rút gọn args để in log cho gọn"""
    if name == "run_terminal":
        cmd = args.get("command", "").strip()
        # Nếu là lệnh Heredoc cũ (nếu có)
        if "cat <<" in cmd and ">" in cmd:
            lines = cmd.splitlines()
            first_line = lines[0]
            target_file = (
                first_line.split(">")[-1].strip().replace("'", "").replace('"', "")
            )
            line_count = max(0, len(lines) - 2)
            return f"[Heredoc] {target_file} ({line_count} lines)"
        # Log ĐẦY ĐỦ lệnh (không cắt cụt) để theo dõi lệnh chạy agent skills,
        # ví dụ: python D:/Inter-K/src/agent_skills/builtin/scripts/render.py <in> <out>
        return " ".join(cmd.split())
    elif name == "write_file":
        path = args.get("path", "")
        content = args.get("content", "")
        line_count = len(content.splitlines())
        return f"path='{path}' ({line_count} lines)"
    elif name == "read_file":
        path = args.get("path", "")
        r = args.get("range")
        extra = []
        if r:
            extra.append(f"range={r}")
        extra_str = f" ({', '.join(extra)})" if extra else ""
        return f"path='{path}'{extra_str}"
    elif name == "str_replace_editor":
        path = args.get("path", "")
        old_str = args.get("old_string", "").replace("\n", "\\n")
        new_str = args.get("new_string", "").replace("\n", "\\n")
        if len(old_str) > 20:
            old_str = f"{old_str[:17]}..."
        if len(new_str) > 20:
            new_str = f"{new_str[:17]}..."
        replace_all = args.get("replace_all", False)
        all_flag = ", replace_all=True" if replace_all else ""
        return f"path='{path}', '{old_str}' -> '{new_str}'{all_flag}"
    # elif name in ("read_image", "read_image_2"):
    #     path = args.get("file_path", "")
    #     box = [args.get(k) for k in ("x1", "y1", "x2", "y2")]
    #     crop = f" crop={box}" if any(v is not None for v in box) else ""
    #     suffix = " scale=0-1000" if name == "read_image_2" else ""
    #     return f"path='{path}'{crop}{suffix}"
    elif name == "grep_search":
        path = args.get("path", "")
        pat = args.get("pattern", "")
        gl = args.get("glob", "")
        mode = args.get("output_mode", "files_with_matches")
        return f"pattern='{pat}' path='{path}' glob='{gl}' mode={mode}"
    # elif name == "render_file":
    #     path=args.get("path","")
    #     return f"path={path}"
    else:
        return str(args)[:50]


def save_message(context: list[dict], msg: dict) -> None:
    """Vừa chèn context vừa append vào file, Chọn JSONL để giữ tốc độ"""
    context.append(msg)
    entry = {"type": "msg", **msg}
    append_turn(entry)


def execute_tool(name: str, args: dict) -> dict:
    """
    Thực thi tool
    """
    tool = TOOLS.get(name, None)
    if not tool or "handler" not in tool:
        return {"success": False, "error": f"KHONG CO TOOL: {name}"}
    return tool["handler"](**args)


def run_agent(context: list[dict]):
    """
    Agent loop chuẩn ReAct
    """
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
            # timeout=120,
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
                    "tool_calls": tool_calls,
                    "reasoning_content": full_reasoning or None,
                    "content": full_text or None,
                },
            )
            # Execute every tool first. Do not append image/user messages yet:
            # every assistant tool_call must be immediately followed by its
            # corresponding role=tool message before any other role appears.
            tool_results = []
            for tc in tool_calls:
                name = tc["function"]["name"]

                try:
                    args = json.loads(tc["function"]["arguments"])
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

                tool_results.append((tc, name, result))

            # Append all tool responses contiguously. This ordering is required
            # by DeepSeek/OpenAI-compatible APIs when multiple tools are called.
            for tc, name, result in tool_results:
                if result.get("type") == "image":
                    tool_content = {
                        "success": result.get("success"),
                        "path": result.get("path"),
                        "type": "image",
                        "mime_type": result.get("mime_type"),
                        "size_bytes": result.get("size_bytes"),
                        "is_compressed": result.get("is_compressed", "No info"),
                        "image_width": result.get("image_width"),
                        "image_height": result.get("image_height"),
                        "region": result.get("region"),
                        "error": result.get("error"),
                        "hint": result.get("hint"),
                    }
                else:
                    tool_content = result

                save_message(
                    context,
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "name": name,
                        "content": json.dumps(tool_content, ensure_ascii=False),
                    },
                )

            # Only after every role=tool message has been appended may image
            # content be sent as a user message for the next model request.
            for tc, name, result in tool_results:
                if result.get("type") != "image":
                    continue

                save_message(
                    context,
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"[IMAGE CONTENT] from {name}"},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": result.get("data_url", ""),
                                    "format": result.get("mime_type", ""),
                                },
                            },
                        ],
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
