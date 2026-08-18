# tool_schema1 = {
#     "type": "function",
#     "function": {
#         "name": "view_image_kcode",
#         "description": "Đọc và render nội dung từ file YAML hoặc từ file mermaid",
#         "parameter": {
#             "type": "object",
#             "properties": {
#                 "path": {
#                     "type": "string",
#                     "description": "đường dẫn tới file yaml hoặc tới mermaid diagram.",
#                 },
#                 "key": {
#                     "type": "string",
#                     "description": "Key trong YAML cần đọc, vd: display để đọc HTML",
#                 },
#             },
#         },
#         "required": [
#             "path",
#         ],
#     },
# }


# tool_schema2 = {
#     "type": "function",
#     "function": {
#         "name": "view_image_kcode",
#         "description": "Đọc và render nội dung html, mermaid diagram hoặc ảnh thuần.",
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "raw_content": {
#                     "type": "string",
#                     "description": "Nội dung cần đọc.",
#                 },
#                 "type": {
#                     "type": "string",
#                     "enum": ["mermaid", "html", "image"],
#                     "description": "Type của nội dung cần đọc.",
#                 },
#             },
#         },
#         "required": ["raw_content", "type"],
#     },
# }


# tool_schema3 = {
#     "type": "function",
#     "function": {
#         "name": "view_image_kcode",
#         "description": (
#             "Đọc file và render nội dung thành ảnh. "
#             "Dùng range để chỉ đọc đoạn cần thiết để render ra ảnh để đọc."
#         ),
#         "parameters": {
#             "type": "object",
#             "properties": {
#                 "path": {
#                     "type": "string",
#                     "description": "Đường dẫn file có content cần render để đọc",
#                 },
#                 "range": {
#                     "type": "array",
#                     "items": {"type": "integer"},
#                     "minItems": 2,
#                     "maxItems": 2,
#                     "description": "[start_line, end_line] - đọc từ dòng start đến dòng end (1-based)",
#                 },
#                 "type": {
#                     "type": "string",
#                     # "enum": ["mermaid", "html", "image"],
#                     "enum": ["mermaid", "html"],
#                     "description": "Type của nội dung cần đọc.",
#                 },
#             },
#         },
#         "required": ["path","range","type"],
#     },
# }


tool_schema_4 = [
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "extract_content_cli",
    #         "description": ("Trích xuất code trong file "),
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "grep_command": {
    #                     "type": "string",
    #                     "description": "Lệnh để trích xuất đoạn code cần thiết",
    #                 },
    #                 "output_path": {
    #                     "type": "string",
    #                     "description": "Đường dẫn file cần được ghi content vào",
    #                 },
    #             },
    #         },
    #         "required": ["path", "grep_command", "output_path"],
    #     },
    # },
    # {
    #     "type": "function",
    #     "function": {"name": "extract_content", "description": ""},
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             "file_path": {"type": "string", "description": ""},
    #             "anchor_head": {"type": "string", "description": ""},
    #             "anchor_tail": {"type": "string", "description": ""},
    #             "validate_only": {"type": "bool", "description": ""},
    #             "line_hint": {
    #                 "type": "array",
    #                 "items": {"type": "integers"},
    #                 "min_items": 2,
    #                 "max_items": 2,
    #                 "description": "",
    #             },
    #             "output_file": {"type": "string", "description": ""},
    #         },
    #     },
    # },
    {
        "type": "function",
        "function": {
            "name": "render_file",
            "description": (
                "Render content trong file .html để chuyển thành ảnh và đưa cho LLM"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Đường dẫn file có content cần render để đọc",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["mermaid", "html"],
                        "description": "Type của nội dung cần render.",
                    },
                },
            },
            "required": ["path", "type"],
        },
    },
]
