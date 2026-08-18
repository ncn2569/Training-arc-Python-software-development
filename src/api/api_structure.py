"""
API structure, học về api của litellm
"""

# finish reason có thể có:
# stop: Model hoàn thành bình thường (gặp stop sequence hoặc kết thúc tự nhiên).
# tool_calls: Model muốn gọi một hoặc nhiều tool.
# --- 2 cái ở dưới chưa gặp ----
# content_filter: Nội dung bị bộ lọc an toàn chặn.
# length: Dừng vì hết max_tokens hoặc giới hạn độ dài.

# {
#     "id": "chatcmpl-565d891b-a42e-4c39-8d14-82a1f5208885",
#     "created": 1734366691,
#     "model": "gpt-5",
#     "object": "chat.completion",
#     "system_fingerprint": null,
#     "choices": [
#         {
#             "finish_reason": "stop",
#             "index": 0,
#             "message": {
#                 "content": "Hello! As an AI language model, I don't have feelings, but I'm operating properly and ready to assist you with any questions or tasks you may have. How can I help you today?",
#                 "role": "assistant",
#                 "tool_calls": null,
#                 "function_call": null
#             }
#         }
#     ],
#     "usage": {
#         "completion_tokens": 43,
#         "prompt_tokens": 13,
#         "total_tokens": 56,
#         "completion_tokens_details": null,
#         "prompt_tokens_details": {
#             "audio_tokens": null,
#             "cached_tokens": 0
#         },
#         "cache_creation_input_tokens": 0,
#         "cache_read_input_tokens": 0
#     }
# }


# ----- KHÔNG CÓ TOOL -------
# ModelResponse(
#     id='cqZparnEJKqC2roPuYbRoAI',
#     created=1785308782,
#     model='gemini-3.5-flash-lite',
#     object='chat.completion',
#     system_fingerprint=None,
#     choices=[
#         Choices(
#             finish_reason='stop',
#             index=0,
#             message=Message(
#                 content='Tôi là một trợ lý AI (trí tuệ nhân tạo), được phát triển bởi Google. Tôi ở đây để hỗ trợ bạn trả lời câu hỏi, tìm kiếm thông tin, viết lách, dịch thuật, lập trình và nhiều việc khác. \n\nTôi có thể giúp gì cho bạn hôm nay?',
#                 role='assistant',
#                 tool_calls=None,
#                 function_call=None,
#                 images=[],
#                 thinking_blocks=[],
#                 provider_specific_fields={
#                     'thought_signatures': ['EjQKMgERTTIPSHHszqZ4UzSTDrm2r/PAorBxbSCHWLodvLyq8CIOQpGK5yCpYJf0K6wMXYvT']
#                 }
#             )
#         )
#     ],
#     usage=Usage(
#         completion_tokens=63,
#         prompt_tokens=5,
#         total_tokens=68,
#         completion_tokens_details=CompletionTokensDetailsWrapper(
#             accepted_prediction_tokens=None,
#             audio_tokens=None,
#             reasoning_tokens=None,
#             rejected_prediction_tokens=None,
#             text_tokens=63,
#             image_tokens=None,
#             video_tokens=None
#         ),
#         prompt_tokens_details=PromptTokensDetailsWrapper(
#             audio_tokens=None,
#             cache_write_tokens=None,
#             cached_tokens=None,
#             text_tokens=5,
#             image_tokens=None,
#             video_tokens=None
#         ),
#         cache_read_input_tokens=None
#     ),
#     vertex_ai_grounding_metadata=[],
#     vertex_ai_url_context_metadata=[],
#     vertex_ai_safety_results=[],
#     vertex_ai_citation_metadata=[],
#     service_tier='default'
# )


# ---- CÓ TOOL ----

# ModelResponse(
#     id='grZpapO4G_Ps2roPxaTZoQY',
#     created=1785312898,
#     model='gemini-3.5-flash-lite',
#     object='chat.completion',
#     system_fingerprint=None,
#     choices=[
#         Choices(
#             finish_reason='tool_calls',
#             index=0,
#             message=Message(
#                 content=None,
#                 role='assistant',
#                 tool_calls=[
#                     ChatCompletionMessageToolCall(
#                         index=0,
#                         provider_specific_fields={
#                             'thought_signature': 'EjQKMgERTTIPjS+KD8d38gWyxps9vDxrGOp/ACOfd8V8FNXQLrdrE4lDSBeBA7oBRRZAS+h0'
#                         },
#                         function=Function(
#                             arguments='{}',
#                             name='read_time'
#                         ),
#                         id='pJYKrPS3__thought__EjQKMgERTTIPjS+KD8d38gWyxps9vDxrGOp/ACOfd8V8FNXQLrdrE4lDSBeBA7oBRRZAS+h0',
#                         type='function'
#                     )
#                 ],
#                 function_call=None,
#                 images=[],
#                 thinking_blocks=[],
#                 provider_specific_fields={
#                     'thought_signatures': ['EjQKMgERTTIPjS+KD8d38gWyxps9vDxrGOp/ACOfd8V8FNXQLrdrE4lDSBeBA7oBRRZAS+h0']
#                 }
#             )
#         )
#     ],
#     usage=Usage(
#         completion_tokens=10,
#         prompt_tokens=91,
#         total_tokens=101,
#         completion_tokens_details=CompletionTokensDetailsWrapper(
#             accepted_prediction_tokens=None,
#             audio_tokens=None,
#             reasoning_tokens=None,
#             rejected_prediction_tokens=None,
#             text_tokens=10,
#             image_tokens=None,
#             video_tokens=None
#         ),
#         prompt_tokens_details=PromptTokensDetailsWrapper(
#             audio_tokens=None,
#             cache_write_tokens=None,
#             cached_tokens=None,
#             text_tokens=91,
#             image_tokens=None,
#             video_tokens=None
#         ),
#         cache_read_input_tokens=None
#     ),
#     vertex_ai_grounding_metadata=[],
#     vertex_ai_url_context_metadata=[],
#     vertex_ai_safety_results=[],
#     vertex_ai_citation_metadata=[],
#     service_tier='default'
# )

# ---STREAMING---
# ModelResponseStream(
#     id="v1hsauPkIfiyvr0P-OmVyAY",
#     created=1785485497,
#     model="gemma-4-31b-it",
#     object="chat.completion.chunk",
#     system_fingerprint=None,
#     choices=[
#         StreamingChoices(
#             finish_reason=None,
#             index=0,
#             delta=Delta(
#                 reasoning_content="The user has provided an empty prompt (or just a blank space).",
#                 provider_specific_fields=None,
#                 content=None,
#                 role="assistant",
#                 function_call=None,
#                 tool_calls=None,
#                 audio=None,
#             ),
#             logprobs=None,
#         )
#     ],
#     provider_specific_fields=None,
#     citations=None,
#     vertex_ai_grounding_metadata=[],
#     vertex_ai_url_context_metadata=[],
#     vertex_ai_safety_ratings=[],
#     vertex_ai_safety_results=[],
#     vertex_ai_citation_metadata=[],
# )


# ----STREAM CHUNK -----

# ModelResponseStream(
#     id="chatcmpl-ab355711b608a535",
#     created=1785720667,
#     model="kCode",
#     object="chat.completion.chunk",
#     system_fingerprint=None,
#     choices=[
#         StreamingChoices(
#             token_ids=None,
#             finish_reason=None,
#             index=0,
#             delta=Delta(
#                 reasoning_content=" sure I'm",
#                 provider_specific_fields=None,
#                 refusal=None,
#                 content=None,
#                 role=None,
#                 function_call=None,
#                 tool_calls=None,
#                 audio=None,
#             ),
#             logprobs=None,
#         )
#     ],
#     provider_specific_fields=None,
#     citations=None,
#     moderation=None,
#     service_tier=None,
# )

# ModelResponseStream(
#     id="chatcmpl-ab355711b608a535",
#     created=1785720667,
#     model="kCode",
#     object="chat.completion.chunk",
#     system_fingerprint="vllm-0.23.1rc1.dev1432+g0231dd546-tp4-ccfa00c9",
#     choices=[
#         StreamingChoices(
#             finish_reason="stop",
#             index=0,
#             delta=Delta(
#                 provider_specific_fields=None,
#                 content=None,
#                 role=None,
#                 function_call=None,
#                 tool_calls=None,
#                 audio=None,
#             ),
#             logprobs=None,
#         )
#     ],
#     provider_specific_fields=None,
#     moderation=None,
#     service_tier=None,
# )

# ModelResponseStream(
#     id="chatcmpl-8a133e57df29bc1a",
#     created=1785721561,
#     model="kCode",
#     object="chat.completion.chunk",
#     system_fingerprint=None,
#     choices=[
#         StreamingChoices(
#             finish_reason=None,
#             index=0,
#             delta=Delta(
#                 provider_specific_fields=None,
#                 refusal=None,
#                 content="",
#                 role="assistant",
#                 function_call=None,
#                 tool_calls=None,
#                 audio=None,
#             ),
#             logprobs=None,
#         )
#     ],
#     provider_specific_fields=None,
#     citations=None,
#     moderation=None,
#     service_tier=None,
#     prompt_token_ids=None,
#     prompt_text=None,
# )

# ModelResponseStream(
#     id="chatcmpl-8a133e57df29bc1a",
#     created=1785721561,
#     model="kCode",
#     object="chat.completion.chunk",
#     system_fingerprint=None,
#     choices=[
#         StreamingChoices(
#             token_ids=None,
#             finish_reason=None,
#             index=0,
#             delta=Delta(
#                 provider_specific_fields=None,
#                 refusal=None,
#                 content=None,
#                 role=None,
#                 function_call=None,
#                 tool_calls=[
#                     ChatCompletionDeltaToolCall(
#                         id="chatcmpl-tool-9c4a1200f24470ec",
#                         function=Function(arguments="{}", name="read_time"),
#                         type="function",
#                         index=0,
#                     )
#                 ],
#                 audio=None,
#             ),
#             logprobs=None,
#         )
#     ],
#     provider_specific_fields=None,
#     citations=None,
#     moderation=None,
#     service_tier=None,
# )

# StreamingChoices(
#     finish_reason="tool_calls",
#     index=0,
#     delta=Delta(
#         provider_specific_fields=None,
#         content=None,
#         role=None,
#         function_call=None,
#         tool_calls=None,
#         audio=None,
#     ),
#     logprobs=None,
# )




#### IMAGE API

# {
#             "role": "user",
#             "content": [
#                             {
#                                 "type": "text",
#                                 "text": "What’s in this image?"
#                             },
#                             {
#                                 "type": "image_url",
#                                 "image_url": {
#                                 "url": "https://awsmp-logos.s3.amazonaws.com/seller-xw5kijmvmzasy/c233c9ade2ccb5491072ae232c814942.png"
#                                 }
#                             }
#                         ]
#         }