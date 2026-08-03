from litellm import completion
import os
import json
import datetime, time
from dotenv import load_dotenv

load_dotenv()

def read_time() -> dict:
    return {
        "success": True,
        "content": datetime.datetime.fromtimestamp(time.time()).isoformat(),
    }
TOOL_DECLARATION = [
    {
        "type": "function",
        "function": {
            "name": "read_time",
            "description": "Read the current date and time in ISO format.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    }
]
# Gọi API với stream=True và có truyền tools
stream = completion(
    model="deepseek/kCode",
    api_key="gw_usr_ce6OA8CtA2mg2c-cQV_97LGwcSUBYGPPHIho8JvsZ0U",
    api_base="https://ai-gateway.inter-k.com/v1",
    messages=[{"role": "user", "content": "Bây giờ là mấy giờ?"}],
    tools=TOOL_DECLARATION,
    stream=False,
)

# for i, chunk in enumerate(stream, start=1):
#     print(f"\n--- [CHUNK #{i}] ---")
    
#     # Cách 1: In trực tiếp Object thô (ModelResponseStream)
#     print(" RAW CHUNK OBJECT:")
#     print(repr(chunk))
    
#     # Cách 2: In riêng object StreamingChoices thô
#     if chunk.choices:
#         choice = chunk.choices[0]
#         print("\n STREAMING CHOICES OBJECT:")
#         print(repr(choice))
        
        # Cách 3: In dạng dict JSON nếu muốn xem cấu trúc key-value
        # print(json.dumps(choice.model_dump(), indent=2, ensure_ascii=False))



print(stream.choices[0].message.tool_calls[0].function)
