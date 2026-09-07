import os
import base64
from dotenv import load_dotenv
from litellm import completion
from litellm.types.utils import Message
from litellm.types.llms.openai import AllMessageValues, ChatCompletionUserMessage
from litellm.litellm_core_utils.token_counter import calculate_img_tokens
from typing import Literal, Optional, List, Any
from pydantic import BaseModel
from dataclasses import dataclass


load_dotenv()
API_KEY = os.getenv("API_KEY")
API_BASE = os.getenv("API_BASE")
MODEL = os.getenv("MODEL")

with open("architecture_overview.png", "rb") as f:
    base64_bytes = f.read()

base64_string = base64.b64encode(base64_bytes).decode("utf-8")

with open("data_flow.png", "rb") as f:
    base64_bytes2 = f.read()

base64_string2 = base64.b64encode(base64_bytes2).decode("utf-8")

img1 = f"data:image/png;base64,{base64_string}"
img2 = f"data:image/png;base64,{base64_string2}"


def _image_message_convert(message: Message) -> dict[str, Any]:
    payload = message.model_dump(mode="json")
    images = payload.pop("images", [])

    if images:
        payload["content"] = [
            {
                "type": "text",
                "text": str(payload.get("content") or ""),
            },
            *images,
        ]

    return payload


# response = completion(
#     model=MODEL,
#     messages=[
#         Message(role="system", content="Bạn là trợ lý AI"),
#         Message(role="user", content="Ảnh này nói về cái gì"),
#         # image_message,
#         _image_message_convert(Message(
#             role="user",
#             content="What's in this message",
#             images=
#                 [
#                     {
#                         "type": "image_url",
#                         "index": 0,
#                         "image_url": {
#                             "url": f"data:image/png;base64,{base64_string}",
#                             "format": "image/png",
#                         },
#                     },
#                     {
#                         "type": "image_url",
#                         "index":1,
#                         "image_url": {
#                             "url": f"data:image/png;base64,{base64_string2}",
#                             "format": "image/png",
#                         }
#                     }
#             ]
#             ,
#         )),
#         Message(role="user", content="1+1 bằng mấy")
#     #     {
#     #         "role": "user",
#     #         "content": [
#     #                         {
#     #                             "type": "text",
#     #                             "text": "What’s in this image?"
#     #                         },
#     #                         {
#     #                             "type": "image_url",
#     #                             "image_url": {
#     #                                 "url": f"data:image/png;base64,{base64_string}",
#     #                                 "format": "image/png",
#     #                             }
#     #                         },
#     #                         {
#     #                             "type": "image_url",
#     #                             "image_url": {
#     #                                 "url": f"data:image/png;base64,{base64_string2}",
#     #                                 "format": "image/png",
#     #                             }
#     #                         }
#     #                     ]
#     #     }
#     # ],
#     # messages=[
#     #     {
#     #         "role": "user",
#     #         "content": [
#     #                         {
#     #                             "type": "text",
#     #                             "text": "What’s in this image?"
#     #                         },
#     #                         {
#     #                             "type": "image_url",
#     #                             "image_url": {
#     #                             "url": f"data:image/png;base64,{base64_string}",
#     #                             "format": "image/png",
#     #                             }
#     #                         }
#     #                     ]
#     #     }
#     ],
#     api_key=API_KEY,
#     # api_base=API_BASE,
# )

response = completion(
    model=MODEL,
    api_key=API_KEY,
    api_base=API_BASE,
    messages = [
        {
            "role": "system",
            "content": "Bạn là trợ lý AI."
        },
        {
            "role": "user",
            "content": "Hãy crop ảnh thành hai vùng trái và phải. Và mô tả nội dung 2 ảnh cho tôi"
        },
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_A",
                    "type": "function",
                    "function": {
                        "name": "crop_image",
                        "arguments": '{"region":"left"}'
                    }
                },
                {
                    "id": "call_B",
                    "type": "function",
                    "function": {
                        "name": "crop_image",
                        "arguments": '{"region":"right"}'
                    }
                }
            ]
        },
        {
            "role": "tool",
            "tool_call_id": "call_A",
            "content": "Tool A completed. Output artifact_A."
        },
        {
            "role": "tool",
            "tool_call_id": "call_B",
            "content": "Tool B completed. Output artifact_B."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "This image is output artifact_A from tool call call_A."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": img1,

                    }
                }
            ]
        },
        
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "This image is output artifact_B from tool call call_B."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": img2
                    }
                }
            ]
        },
    ]
)

print(response.choices[0].message.content)


# with open("browserless-external-assets-test.png", "rb") as f:
#     base64_bytes1 = f.read()

# base64_string1 = base64.b64encode(base64_bytes1).decode("utf-8")

# img_string = f"data:image/png;base64,{base64_string1}"

# print(calculate_img_tokens(
#     data=img_string,
#     mode="auto",
#     use_default_image_token_count=not img_string.startswith(
#         "data:"),
# ))


# def _to_llm_message(message: Message) -> dict[str, Any]:
#     """Convert a history message to the LiteLLM request payload."""
#     payload = message.model_dump(mode="json")
#     images = payload.pop("images", [])
#     if images:
#         images = [
#             {key: value for key, value in image.items() if key != "index"}
#             for image in images
#         ]
#         payload["content"] = [
#             {
#                 "type": "text",
#                 "text": str(payload.get("content") or ""),
#             },
#             *images,
#         ]
#     return payload

# temp = [
#     _to_llm_message(Message(role="system", content="Bạn là trợ lý AI")),
#     _to_llm_message(Message(role="user", content="Ảnh này nói về cái gì")),
#     _to_llm_message(
#         Message(
#             role="user",
#             content="What's in this message",
#             images=[
#                 {
#                     "type": "image_url",
#                     "index": 0,
#                     "image_url": {
#                         "url": f"data:image/png;base64,{base64_string}",
#                         "format": "image/png",
#                     },
#                 },
#                 {
#                     "type": "image_url",
#                     "index": 1,
#                     "image_url": {
#                         "url": f"data:image/png;base64,{base64_string2}",
#                         "format": "image/png",
#                     },
#                 },
#             ],
#         )
#     ),
# ]

# print(temp)


# [
#     {
#         "content": "Bạn là trợ lý AI",
#         "role": "system",
#         "tool_calls": None,
#         "function_call": None,
#         "provider_specific_fields": None,
#     },
#     {
#         "content": "Ảnh này nói về cái gì",
#         "role": "user",
#         "tool_calls": None,
#         "function_call": None,
#         "provider_specific_fields": None,
#     },
#     {
#         "content": [
#             {"type": "text", "text": "What's in this message"},
#             {
#                 "image_url": {
#                     "url": "data:image/png;base64,iVBORw0KGg",
#                     "format": "image/png",
#                 },
#                 "type": "image_url",
#             },
#             {
#                 "image_url": {
#                     "url": "data:image/png;base64,iVBORw0KGg",
#                     "format": "image/png",
#                 },
#                 "type": "image_url",
#             },
#         ],
#         "role": "user",
#         "tool_calls": None,
#         "function_call": None,
#         "provider_specific_fields": None,
#     },
# ]
# response = completion(
#     model=MODEL,
#     api_key=API_KEY,
#     messages=temp
# )

# print(response.choices[0].message.content)
