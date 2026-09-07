import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from litellm import completion

THRESHOLD = 100000000000# int(256000 * 0.75)  # nguồn :))) hỏi nó

# max_token=get_max_token(model="openai/kCode")
# THRESHOLD = int(maxtoken*0.75)

SESSIONS_DIR = (Path(__file__).parent.parent.parent / "sessions").resolve()
SESSION_FILE = SESSIONS_DIR / "session.jsonl"  # session hiện tại
ARCHIVE_DIR = SESSIONS_DIR / "archive"  # session cũ -- nghiên cứu thêm sau có thể là db


def ensure_dirs() -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def session_exists() -> bool:
    return SESSION_FILE.exists() and SESSION_FILE.stat().st_size > 0


def archive_session() -> None:
    ensure_dirs()
    if SESSION_FILE.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = ARCHIVE_DIR / f"session_{ts}.jsonl"
        shutil.move(str(SESSION_FILE), str(dest))


def append_turn(entry: dict) -> None:
    ensure_dirs()

    line = json.dumps(entry, ensure_ascii=False) + "\n"

    with open(SESSION_FILE, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()


def load_context() -> list[dict]:
    if not SESSION_FILE.exists():
        return []

    messages = []
    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        line = line.strip()

        if not line:
            continue

        try:
            data = json.loads(line)
            if data.get("type") == "msg":
                msg = {k: v for k, v in data.items() if k != "type"}
                messages.append(msg)
        except json.JSONDecodeError:
            if i == len(lines) - 1:
                print(f"Dòng cuối corrupt -- Ctrl C, bỏ qua")
            else:
                print(f"Dòng {i + 1} JSON lỗi, bỏ qua")

    fixed_message = fix_orphan_tool_calls(messages)

    if len(fixed_message) > len(messages):
        new_orphan_msgs = fixed_message[len(messages) :]
        for msg in new_orphan_msgs:
            append_turn({"type": "msg", **msg})

    return fixed_message


def count_tokens(context: list[dict]) -> int:
    """
    Xấp xỉ: CTHUC= len(json_string.encode("utf-8")) // 3 tiếng việt
    """
    text = json.dumps(context, ensure_ascii=False)
    return len(text.encode("utf-8")) // 3  # 3 bytes 1 token
    # return token_counter(model="openai/kCode", message=context)

def count_tokens_by_string(text: str) -> int:
    return len(text.encode("utf-8")) // 3


def rewrite_session(new_context: list[dict]) -> None:
    archive_session()
    for msg in new_context:
        entry = {"type": "msg", **msg}
        append_turn(entry)


COMPACTION_PROMPT = """
Bạn là bộ nhớ tổng hợp hội thoại của AI Agent.
Nhiệm vụ của bạn là tạo một bản TÓM TẮT TÍCH LŨY ngắn gọn bằng tiếng Việt.
ĐẮC BIỆT LƯU Ý:
Nếu trong đoạn hội thoại có chứa bản tóm tắt cũ (`--- [TÓM TẮT CÁC TURN TRƯỚC ĐÂY] ---`), bạn PHẢI đọc và gộp các thông tin từ bản tóm tắt cũ đó với các tin nhắn mới để tạo ra một bản tóm tắt mới HOÀN CHỈNH TỔNG THỂ từ đầu đến giờ.
Nội dung cần giữ lại:
1. Yêu cầu/mục tiêu chính của master Nguyen
2. Danh sách tất cả file/thư mục đã tạo hoặc chỉnh sửa từ trước đến nay
3. Các lỗi từng gặp và cách khắc phục
4. Trạng thái công việc hiện tại (đã làm xong gì, việc gì cần làm tiếp theo)
CHỈ trả về duy nhất đoạn tóm tắt, không thêm lời chào hay giải thích nào khác.
"""


def compact_context(
    context: list[dict],
    api_key: str,
    api_base: str,
    model: str,
    keep_num: int = 15,  # hơi hard code
) -> list[dict]:
    """
    context = sys + (user + assistant + tools)^n --> context = [sys + (user + assistant + tools)^n-5 ]-- (new system prompt) + (user+assistant+tool)^5
    """

    system_msg = context[0]
    keep_count = min(keep_num, len(context) - 1)
    keep_messages = context[-keep_count:]
    to_summarize = context[1:-keep_count]

    # if len(to_summarize) == 0:
    #     return context

    try:
        print("[COMPACTING....] đang compact")
        response = completion(
            model=model,
            api_key=api_key,
            api_base=api_base,
            messages=[
                {"role": "system", "content": COMPACTION_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(to_summarize, ensure_ascii=False, indent=2),
                },
            ],
        )

        summary = response.choices[0].message.content.strip()

    except Exception as e:
        print(
            f"model nén bị lỗi {str(e)}, cắt khúc to_summarize"
        )  ## nghiên cứu thêm cơ chế retry
        return [system_msg] + keep_messages

    summary_context = {
        "role": "user",
        "content": (
            f"--- [TÓM TẮT CÁC TURN TRƯỚC ĐÂY] ---\n"
            f"{summary}\n"
            f"-----------------------------------"
        ),
    }
    # SYSTEMPROMPT + summary-stacked

    new_context = [system_msg, summary_context] + keep_messages

    rewrite_session(new_context)

    return new_context


def fix_orphan_tool_calls(context: list[dict]) -> list[dict]:
    """
    check xem tool đang mồ côi :)))
    """
    result = []
    pending = {}

    for msg in context:
        role = msg.get("role", "")
        if role == "assistant" and msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                # tool_call_id : tool_call (id:str,type:str,function:dict)
                pending[tc["id"]] = tc

            result.append(msg)
        elif role == "tool":
            pending.pop(msg.get("tool_call_id", ""), None)

            result.append(msg)

        # user+system+assistant thường
        else:
            _flush_orphans(result, pending)

            result.append(msg)

    _flush_orphans(result, pending)
    return result


def _flush_orphans(result: list[dict], pending: dict) -> None:
    """
    ánh xạ tool vào context tương ứng với tool_id + tool_name
    """
    for orphan_id, tc in pending.items():
        orphan_name = tc.get("function", {}).get("name", "")
        cmd = tc.get("function", {}).get("arguments", "")
        error_msg = {
            "role": "tool",
            "tool_call_id": orphan_id,
            "name": orphan_name,
            "content": json.dumps(
                {
                    "success": False,
                    "crash_command": cmd,
                    "error": (
                        "AGENT_CRASHED_DURING_TOOL_EXECUTION: Agent bị crash "
                        "NẾU LỆNH NÀY AN TOÀN (KHÔNG CÓ SIDE-EFFECT: ls, whoami,...) THÌ BẠN CÓ THỂ RETRY"
                        "NẾU LỆNH NÀY NGUY HIỂM (CÓ SIDE-EFFECT: rm, del, rmdir,....) THÌ HÃY KIỂM TRA TRẠNG THÁI TRƯỚC KHI CHẠY LẠI."
                    ),
                },
                ensure_ascii=False,
            ),
        }
        result.append(error_msg)

    pending.clear()
