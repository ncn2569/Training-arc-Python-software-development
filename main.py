from src.agent_skills.loader import build_system_prompt
from src.context.memory import (
    append_turn,
    archive_session,
    load_context,
    session_exists,
)
from src.context.prompt import SYSTEM_PROMPT
from src.core.agent import run_agent, save_message

# Bơm danh sách Agent Skills (name + description) vào system prompt ngay từ đầu
# để agent biết có những skill nào; nội dung đầy đủ chỉ nạp khi gọi `load_skill`.
SYSTEM_PROMPT_WITH_SKILLS = build_system_prompt(SYSTEM_PROMPT)


def main() -> None:
    """Hàm entry point chính — khởi tạo session và chạy agent loop."""
    if session_exists():
        ans = input("Có session cũ. Resume? (y/n): ").strip().lower()
        if ans == "y":
            context = load_context()
            print(f"Resume session: {len(context)} messages")
        else:
            archive_session()
            context = [{"role": "system", "content": SYSTEM_PROMPT_WITH_SKILLS}]
            append_turn({"type": "msg", "role": "system", "content": SYSTEM_PROMPT_WITH_SKILLS})
            print("Session mới đã được tạo.\n")
    else:
        context = [{"role": "system", "content": SYSTEM_PROMPT_WITH_SKILLS}]
        append_turn({"type": "msg", "role": "system", "content": SYSTEM_PROMPT_WITH_SKILLS})

    while True:
        try:
            prompt = input("Bạn: ").strip()

        except (EOFError, KeyboardInterrupt):
            print(
                f"\n Context đã lưu ({len(context)} messages). Tạm biệt master Nguyen!"
            )
            break

        if prompt.lower() in {"exit", ""}:
            print(f" Context đã lưu ({len(context)} messages). Tạm biệt master Nguyen!")
            break

        save_message(context, {"role": "user", "content": prompt})

        try:
            run_agent(context)
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")

if __name__ == "__main__":
    main()