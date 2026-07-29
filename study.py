import json
import os
import subprocess
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# from litellm import completion  # tạm gác lại tutu nghiên cứu

# response = completion(
#     model="gemini/gemini-3.5-flash-lite",
#     api_key=os.getenv("api_key"),
#     messages=[
#         {"role": "user", "content": prompt}
#     ]
# )


def read_time() -> dict:
    return {"success": True, "content": time.time()}


TOOLS = {
    "read_file": {"type": "cli", "command": "read_file_cli.py"},
    "read_time": {"type": "python", "handler": read_time},
}


TOOL_DECLARATIONS = [
    {
        "type": "function",
        "name": "read_file",
        "description": "Read the content of a text file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "the file path that need to be read",
                }
            },
            "required": ["path"],
        },
    },
    {
        "type": "function",
        "name": "read_time",
        "description": "Read the current time",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
]

# def print_agent_thoughts(interaction, step_number: int):
#     print(f"\n--- [SUY NGHĨ BƯỚC {step_number}] ---")
#     for step in interaction.steps:
#         # Kiểm tra nếu step là dạng 'thought'
#         if step.type == "thought":
#             # In nội dung suy nghĩ (hoặc summary nếu có)
#             thought_text = getattr(step, "text", None) or getattr(step, "summary", None) or step
#             print(f"Thought: {thought_text}")
#         elif step.type == "function_call":
#             print(f"Quyết định gọi Tool: {step.name}({step.arguments})")
#         elif step.type == "model_output":
#             print(f"Quyết định câu trả lời cho User.")
#     print("------------------------------------\n")

load_dotenv()

client = genai.Client(api_key=os.getenv("api_key"))


def execute_tool(name: str, args: dict):
    tool = TOOLS[name]
    if tool is None:
        return {"success": False, "error": f"Khong co tool: {name}"}

    if tool["type"] == "cli":
        result = subprocess.run(
            ["python", tool["command"], args["path"]], capture_output=True, text=True
        )

    elif tool["type"] == "python":
        return tool["handler"](**args)

    return json.loads(result.stdout)


def format_message_to_string(message: list[dict]) -> str:
    parts = []
    for msg in message:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            parts.append(f"[System prompt]\n{content}")
        elif role == "user":
            parts.append(f"[User prompt]\n{content}")
        elif role == "assistant":
            parts.append(f"[AI answer]\n{content}")
    return "\n\n--\n\n".join(parts)


def run_agents(messages: list[dict], max_steps: int = 10):
    formatted_prompt = format_message_to_string(messages)

    interaction = client.interactions.create(
        model="gemini-3.5-flash-lite",
        input=formatted_prompt,
        tools=TOOL_DECLARATIONS,
    )

    for step_count in range(max_steps):

        # print_agent_thoughts(interaction, step_count + 1)

        function_call = [step for step in interaction.steps if step.type == "function_call"]

        print(interaction.steps)

        if not function_call:
            return interaction.output_text

        function_results = []
        for call in function_call:
            try:
                result = execute_tool(call.name, call.arguments)
            except Exception as e:
                result = {"success": False, "error": str(e)}
            function_results.append(
                {
                    "type": "function_result",
                    "name": call.name,
                    "call_id": call.id,
                    "result": result,
                }
            )

        interaction = client.interactions.create(
            model="gemini-3.5-flash-lite",
            #server quản lý, Hay vleu nma chắc phải học cách tự quản lý
            previous_interaction_id=interaction.id,  
            tools=TOOL_DECLARATIONS,
            input=function_results
        )
    return "Nhiều hơn max steps rồi"


messages = [
    {"role": "system", "content": "Bạn là trợ lý AI hữu ích"}
]  # conversational context


while True:
    prompt = input("Bạn: ").strip()
    if prompt.lower() in {"exit", ""}:
        break

    messages.append({"role": "user", "content": prompt})

    try:
        answer = run_agents(messages)
        print(messages)
        messages.append({"role": "assitant", "content": answer})
        print("AI: ", answer)
    except Exception as e:
        print(e)
