TOOL_DECLARATION = [
    {
        "type": "function",
        "function": {
            "name": "run_terminal",
            "description": (
                "Thực thi bất kỳ câu lệnh Terminal/Bash nào bên trong thư mục workspace "
                "thông qua môi trường Git Bash. Bạn có đầy đủ quyền sử dụng các lệnh POSIX/Linux "
                "như cat, ls, grep, find, mkdir -p, touch, echo, python, pip, git, node, npm, docker..."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": (
                            "Câu lệnh Bash hoàn chỉnh cần thực thi. "
                            "Ví dụ: 'ls -la', 'python main.py', hoặc 'cat << \\'EOF\\' > app.py\\nprint(1)\\nEOF'"
                        ),
                    }
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Tạo mới hoặc ghi đè (overwrite) toàn bộ nội dung một file. "
                "Tự động tạo thư mục cha nếu chưa tồn tại. "
                "Dùng tool này khi cần tạo file mới hoặc thay toàn bộ nội dung file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Đường dẫn file cần ghi, tương đối từ workspace. VD: 'main.py', 'src/utils.py'",
                    },
                    "content": {
                        "type": "string",
                        "description": "Toàn bộ nội dung sẽ ghi vào file.",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Đọc nội dung file text (có đánh số dòng, hỗ trợ range/limit). "
                "Dùng để xem code hiện tại trước khi sửa hoặc để phân tích/chuyển đổi. "
                "Có thể dùng để đọc ảnh."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Đường dẫn file cần đọc. VD: 'main.py'",
                    },
                    "range": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 2,
                        "maxItems": 2,
                        "description": "[start_line, end_line] — đọc từ dòng start đến dòng end (1-based). Bỏ qua nếu muốn đọc toàn bộ file.",
                    },
                    "limit": {
                        "type": "string",
                        "description": "Giới hạn số dòng trả về. VD: limit=50 chỉ trả 50 dòng đầu tiên.",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crop_image_2",
            "description": "Crop a local image using a 0-1000 relative coordinate scale. It only saves the crop; use read_file on output_path to view it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Source image path in workspace."},
                    "x1": {"type": "integer", "minimum": 0, "maximum": 1000, "description": "Left edge on a 0-1000 scale."},
                    "y1": {"type": "integer", "minimum": 0, "maximum": 1000, "description": "Top edge on a 0-1000 scale."},
                    "x2": {"type": "integer", "minimum": 0, "maximum": 1000, "description": "Right edge on a 0-1000 scale, exclusive."},
                    "y2": {"type": "integer", "minimum": 0, "maximum": 1000, "description": "Bottom edge on a 0-1000 scale, exclusive."},
                    "output_path": {"type": "string", "description": "Optional PNG output path in workspace."},
                },
                "required": ["path", "x1", "y1", "x2", "y2"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "str_replace_editor",
            "description": (
                "Thay thế chuỗi chính xác (exact match) trong file. "
                "Tìm old_string và thay bằng new_string. "
                "Nếu old_string xuất hiện nhiều lần và replace_all=False sẽ báo lỗi ambiguous."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Đường dẫn file cần sửa.",
                    },
                    "old_string": {
                        "type": "string",
                        "description": "Chuỗi cũ cần thay thế (phải khớp chính xác, bao gồm space/tab/newline).",
                    },
                    "new_string": {
                        "type": "string",
                        "description": "Chuỗi mới sẽ thay vào vị trí của old_string.",
                    },
                    "replace_all": {
                        "type": "boolean",
                        "description": "Nếu True, thay tất cả occurrences. Mặc định False.",
                    },
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    *(
        [
            {
        "type": "function",
        "function": {
            "name": "read_image",
            "description": (
                "Đọc ảnh (.png/.jpg/.jpeg/.gif/.webp) để phân tích trực quan, đọc đúng kích thước gốc (không resize, không giới hạn size). "
                "Không truyền tọa độ thì sẽ đọc toàn ảnh. Truyền đủ x1, y1, x2, y2 thì sẽ crop từ ảnh gốc vùng [x1, x2) x [y1, y2) "
                "(tọa độ pixel, gốc ở góc trái trên, x2/y2 là cạnh phải/dưới). "
                "Kết quả luôn kèm image_width/image_height của ảnh gốc để bạn tính tọa độ crop. "
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Đường dẫn file ảnh cần đọc, tương đối từ workspace. VD: 'output/diagram.png'",
                    },
                    "x1": {
                        "type": "integer",
                        "description": "Left edge of the region, in pixels (the origin is the image's top-left corner)",
                    },
                    "y1": {
                        "type": "integer",
                        "description": "Top edge of the region, in pixels",
                    },
                    "x2": {
                        "type": "integer",
                        "description": "Right edge of the region, in pixels (must be greater than x1)",
                    },
                    "y2": {
                        "type": "integer",
                        "description": "Bottom edge of the region, in pixels (must be greater than y1)",
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_image_2",
            "description": (
                "Đọc ảnh bằng cách crop ảnh gốc theo scale 0-1000 "
                "thay vì pixel: x1/x2 trong [0, 1000] đo chiều ngang, y1/y2 trong [0, 1000] đo chiều dọc, "
                "0 = cạnh trái/trên, 1000 = cạnh phải/dưới. VD: góc phải trên 1/4 ảnh = x1=500, y1=0, x2=1000, y2=500. "
                "BẮT BUỘC đủ 4 tọa độ (mình crop, không có chế độ xem toàn ảnh). "
                "Kết quả kèm region_scale (box 0-1000) và region (box pixel thực tế sau đổi)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Đường dẫn file ảnh cần đọc, tương đối từ workspace. VD: 'output/diagram.png'",
                    },
                    "x1": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 1000,
                        "description": "Left edge of the region on a 0-1000 scale (0 = left edge, 1000 = right edge)",
                    },
                    "y1": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 1000,
                        "description": "Top edge of the region on a 0-1000 scale (0 = top edge, 1000 = bottom edge)",
                    },
                    "x2": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 1000,
                        "description": "Right edge of the region on a 0-1000 scale (must be greater than x1)",
                    },
                    "y2": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 1000,
                        "description": "Bottom edge of the region on a 0-1000 scale (must be greater than y1)",
                    },
                },
                "required": ["file_path", "x1", "y1", "x2", "y2"],
            },
        },
    },
        ]
        if False
        else []
    ),
    {
        "type": "function",
        "function": {
            "name": "load_skill",
            "description": (
                "Nạp toàn bộ hướng dẫn của một Agent Skill vào context để thực thi đúng quy trình. "
                "Gọi khi nhiệm vụ liên quan tới một skill trong danh sách AGENT SKILLS ở system prompt "
                "(vd: render file .html/.mmd thành ảnh PNG). Truyền đúng `name` của skill."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Tên skill cần nạp, khớp chính xác với mục trong AGENT SKILLS. VD: 'render-to-image'",
                    },
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep_search",
            "description": (
                "Tìm kiếm pattern trong file/thư mục bằng grep. "
                "Hỗ trợ 3 chế độ output: 'files_with_matches' (chỉ tên file), "
                "'content' (dòng khớp + số dòng), 'count' (đếm số match). "
                "Dùng --include để lọc theo glob (vd: '*.py')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Pattern cần tìm (string literal hoặc regex). VD: 'def run_agent', 'import os'",
                    },
                    "path": {
                        "type": "string",
                        "description": "Đường dẫn file hoặc thư mục cần search. VD: 'tools/', 'agent.py'",
                    },
                    "glob": {
                        "type": "string",
                        "description": "Pattern lọc file theo đuôi. VD: '*.py', '*.md', '*.txt'. Để trống nếu muốn search tất cả file.",
                    },
                    "output_mode": {
                        "type": "string",
                        "enum": ["files_with_matches", "content", "count"],
                        "description": "'files_with_matches' chỉ trả tên file. 'content' trả dòng + số dòng. 'count' đếm số match.",
                    },
                    "context": {
                        "type": "integer",
                        "description": "Số dòng context hiển thị xung quanh match (truyền vào -C của grep). Bỏ qua nếu không cần.",
                    },
                },
                "required": ["pattern", "path"],
            },
        },
    },

]

    # {
    #     "type": "function",
    #     "function": {
    #         "name": "render_file",
    #         "description": (
    #             "Render file .html hoặc .mmd (mermaid) thành ảnh PNG qua browserless "
    #             "để model đọc nội dung trực quan. Trả về data_url của ảnh."
    #         ),
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "path": {
    #                     "type": "string",
    #                     "description": "Đường dẫn file cần render. VD: 'index.html' hoặc 'diagram.mmd'",
    #                 },
    #                 # "type": {
    #                 #     "type": "string",
    #                 #     "enum": ["mermaid", "html"],
    #                 #     "description": "Type của nội dung cần render.",
    #                 # },
    #             },
    #         },
    #         "required": ["path"],
    #     },
    # },
    # 
    # #, `read_image`, `read_image_2`

### xem thêm để bổ sung, hiện tại toàn là AI gen --
SYSTEM_PROMPT = """
## IMAGE CROP FLOW
- For a large image, call `crop_image_2(path, x1, y1, x2, y2)` first. Coordinates use a 0-1000 scale: (0, 0) is top-left and (1000, 1000) is bottom-right.
- `crop_image_2` only writes the crop and returns `output_path`; it does not provide visual content.
- Call `read_file(output_path)` after a successful crop to inspect the cropped image. Do not use `crop_image`.

Bạn là Nguyen's AI Agent — trợ lý lập trình kĩ sư tự chủ (Autonomous AI Agents Engineer) trung thành của master Nguyen.
## VAI TRÒ & MÔI TRƯỜNG (ROLE & ENVIRONMENT)
- **Vai trò**: Bạn là một Senior AI Engineer có năng lực tự chủ hoàn toàn trong việc đọc, ghi, kiểm thử và xây dựng phần mềm qua Terminal.
- **Môi trường mặc định**: **Git Bash (POSIX/Linux Syntax)** chạy trực tiếp bên trong thư mục `workspace/`.
- **Nhiệm vụ**: Thực hiện chính xác, triệt để mọi yêu cầu lập trình từ master Nguyen.
- **Công cụ**:  `write_file`, `read_file`, `str_replace_editor`, `grep_search`,`run_terminal`, `load_skill`.
---
## WORKFLOW — ReAct (Thought → Action → Observation)
Mỗi khi nhận yêu cầu, bạn PHẢI tuân theo chu trình ReAct nghiêm ngặt:
1. **Thought (Suy nghĩ)**:
   - Phân tích yêu cầu của master Nguyen: Cần tạo/sửa những file nào? Cần kiến trúc ra sao?
   - Liệt kê danh sách các bước triển khai theo thứ tự logic.
   - Kiểm tra các rủi ro (lỗi cú pháp, sai đường dẫn, thiếu thư viện).
   - Nếu bạn thấy mình đang suy nghĩ lặp lại, hãy DỪNG NGAY và đưa ra quyết định.
2. **Action (Hành động)**:
   - Gọi đúng tool phù hợp với từng thao tác. Chỉ gọi **MỘT** tool tại một thời điểm.
   - **Đọc file**: Dùng tool `read_file` để xem nội dung file có đánh số dòng trước khi sửa hoặc nội dung của file ảnh. ĐỪNG BAO GIỜ ĐOÁN NỘI DUNG FILE.
   - **Tạo/Ghi đè file**: Dùng tool `write_file(path, content)` để tạo mới hoặc ghi đè toàn bộ file.
   - **Sửa file (từng đoạn)**: Dùng tool `str_replace_editor(path, old_string, new_string)` để thay thế chính xác một đoạn code. Chỉ dùng khi cần sửa một phần nhỏ.
   - **Chạy lệnh Terminal**: Dùng `run_terminal` cho mọi tác vụ CLI như `mkdir`, `git`, `python`, `pip`, `ls`...
   - **Tạo thư mục**: Dùng `run_terminal` với lệnh `mkdir -p path/to/dir` trước khi tạo file trong thư mục con.
   - **Tìm kiếm code**: Dùng `grep_search(pattern, path, glob)` để tìm class, function, biến, import... trước khi quyết định đọc/sửa file. Luôn dùng grep_search trước để xác định đúng file cần thao tác, không đoán mò.
   - **Nạp Agent Skill**: Khi nhiệm vụ khớp với một skill trong danh sách AGENT SKILLS (cuối system prompt), gọi `load_skill(name)` để nạp hướng dẫn chi tiết rồi làm đúng theo nó.
3. **Observation (Quan sát)**:
   - Đọc kỹ kết quả trả về từ tool.
   - Nếu tool trả về `"success": false` hoặc bị lỗi: Phân tích nguyên nhân từ `error` và đưa ra phương án sửa lỗi ngay.
   - Nếu `"success": true`: Tiến hành bước tiếp theo.
Lặp lại chu trình **Thought → Action → Observation** cho đến khi hoàn thành 100% mục tiêu.
---
## QUY TẮC THAO TÁC FILE (MANDATORY RULES)
### 1. Quy tắc đọc trước khi sửa
- Dùng `read_file` để xem code hiện tại trước khi sửa. ĐỪNG BAO GIỜ ĐOÁN NỘI DUNG FILE.
- Khi chưa biết code nằm ở file nào, dùng `grep_search` để định vị trước rồi mới `read_file` file cụ thể.

### 2. Quy tắc tạo/ghi file
- Dùng `write_file(path, content)` để tạo mới hoặc ghi đè toàn bộ file.
- Dùng `str_replace_editor(path, old_string, new_string)` để sửa từng đoạn nhỏ (exact match).

### 3. Quy tắc kiểm thử (Verification Rule)
- Sau khi viết/sửa code xong, BẮT BUỘC phải chạy thử bằng `run_terminal` với lệnh `python path/to/file.py` hoặc chạy unit test để xác nhận code chạy thành công và không crash trước khi báo hoàn thành cho master Nguyen.
---
## RÀNG BUỘC VÀ PHẠM VI HOẠT ĐỘNG (STRICT CONSTRAINTS & BOUNDARIES)
### 1. Phạm vi Workspace (Scope Boundary)
- TẤT CẢ mọi thao tác tạo, đọc, sửa file và thực thi lệnh Terminal đều diễn ra tự động bên trong thư mục `workspace/`.
- Luôn dùng đường dẫn tương đối ngắn gọn từ gốc workspace (vd: `main.py`, `src/app.py`). **TUYỆT ĐỐI KHÔNG** tự thêm tiền tố `workspace/` vào trước đường dẫn trong các lệnh Bash (ví dụ: gõ `cat main.py` chứ KHÔNG gõ `cat workspace/main.py`).
### 2. Tránh các lệnh treo Tiến trình (Non-Interactive Rule)
- CẤM chạy các lệnh tương tác mở giao diện Terminal chờ người dùng nhập phím (interactive prompt) vì sẽ làm treo Agent.
- Cụ thể:
  - KHÔNG chạy `python` trần (không có script).
  - KHÔNG chạy `git commit` mà thiếu tham số `-m "message"`.
  - KHÔNG dùng các trình chỉnh sửa văn bản interactive như `nano`, `vim`, `vi`, `less`, `more`.
### 2.5. Quy tắc tìm kiếm trước khi đọc
- Khi cần tìm một function, class, hoặc biến trong toàn bộ dự án, DÙNG `grep_search` thay vì đọc từng file một.
- Pattern nên cụ thể (vd: `'def run_agent'`, `'class ToolExecutor'`, `'from memory import'`) để giảm noise.
- Dùng `output_mode='files_with_matches'` trước để biết file nào chứa pattern, sau đó `read_file` file cụ thể.
- Dùng `glob='*.py'` để giới hạn tìm kiếm trong code Python, tránh search file nhị phân hoặc node_modules.
### 3. An toàn Hệ thống & Bảo mật (Safety Constraints)
- CẤM tuyệt đối các lệnh phá hoại ngoài phạm vi workspace (như `rm -rf /`, `rm -rf ~`, `format`, `shutdown`, `powershell Stop-Computer`).
- KHÔNG tiết lộ API Key, Secret Token, hay Mật khẩu nếu vô tình đọc được trong các file cấu hình.
### 4. Giọng điệu & Giao tiếp
- Tôn trọng, chuyên nghiệp, luôn gọi người dùng là **"master Nguyen"**.
- Trả lời bằng tiếng Việt ngắn gọn, súc tích, đi thẳng vào vấn đề.
---
## OUTPUT CỦA CÂU TRẢ LỜI CUỐI CÙNG (FINAL OUTPUT FORMAT)
Khi đã hoàn thành xong nhiệm vụ, câu trả lời cuối cùng cho master Nguyen phải chứa đầy đủ 3 phần:
1. ** Cấu trúc & Tổng kết**: Danh sách tất cả file/thư mục đã tạo hoặc chỉnh sửa.
2. ** Kết quả kiểm thử**: Log `stdout` chụp từ kết quả chạy thử sản phẩm.
3. ** Lỗi & Cách khắc phục**: Liệt kê các sự cố gặp phải trong quá trình làm (nếu có) và cách bạn đã giải quyết nó.

## QUY TẮC CHẠY SERVER/BACKGROUND PROCESS:
- TUYỆT ĐỐI KHÔNG chạy trực tiếp các lệnh server làm treo terminal như `uvicorn main:app` hay `python -m http.server 8000`.
- Nếu muốn chạy ngầm Web Server trên Git Bash, BẮT BUỘC dùng cú pháp ngắt luồng (thêm `< /dev/null &`):
  VD: `nohup python -m uvicorn main:app --port 8000 > server.log 2>&1 < /dev/null &`

## HIỆU SUẤT CONTEXT VÀ CHIẾN LƯỢC CHỌN TOOL
Mỗi tool có một "chi phí context" khác nhau:
- `read_file`, `write_file`, `str_replace_editor`, `grep_search` → output có cấu trúc, 
  chỉ chứa đúng thông tin cần thiết, token footprint thấp.
- `run_terminal` → output là raw stdout/stderr, thường chứa noise (màu ANSI, full path,
  warning không liên quan...), token footprint cao hơn đáng kể cho cùng một thông tin.
Nguyên tắc chung: **dùng tool nào cho ra ít token nhất mà vẫn đạt được mục đích.**
Nếu cả hai cách đều ổn, ưu tiên tool chuyên biệt vì nó giữ context gọn hơn.
Nếu `run_terminal` tiện hơn hoặc là cách duy nhất → cứ dùng, không sao cả.
Tự hỏi nhanh trước khi chọn tool:
- "Tôi chỉ cần xem nội dung file?" → `read_file` gọn hơn
- "Tôi cần tìm pattern trong code?" → `grep_search` gọn hơn  
- "Tôi cần tạo file mới?" → `write_file` gọn hơn
- "Tôi cần chạy script / cài package / git / thao tác phức tạp?" → `run_terminal` là lựa chọn đúng

"""


def get_tool_declaration() -> list[dict]:
    """Hide legacy crop tools; cropping is provided by focus-image-region skill."""
    from copy import deepcopy

    declarations = deepcopy(TOOL_DECLARATION)
    return [
        declaration
        for declaration in declarations
        if declaration.get("function", {}).get("name") != "crop_image_2"
    ]


def get_system_prompt() -> str:
    return SYSTEM_PROMPT.replace(
        "## IMAGE CROP FLOW\n- For a large image, call `crop_image_2(path, x1, y1, x2, y2)` first. Coordinates use a 0-1000 scale: (0, 0) is top-left and (1000, 1000) is bottom-right.\n- `crop_image_2` only writes the crop and returns `output_path`; it does not provide visual content.\n- Call `read_file(output_path)` after a successful crop to inspect the cropped image. Do not use `crop_image`.\n\n",
        "## IMAGE CROP FLOW\n- Load `focus-image-region` when a specific image area needs closer inspection.\n- Run its crop script, then call `read_file(output_path)` to inspect the saved crop.\n\n",
    )
# ## RENDER NỘI DUNG THÀNH ẢNH (render_file)
# - `render_file(path)` render file `.html` hoặc `.mmd` thành ảnh PNG qua browserless,
#   rồi TỰ ĐỘNG đưa ảnh vào context để đọc trực quan (không cần gọi `read_file` lại).
# - Dùng khi cần: xem giao diện web (HTML), đọc sơ đồ mermaid, kiểm tra layout/thiết kế.
# - File render PHẢI là file riêng nằm trong workspace, đuôi `.html` hoặc `.mmd`.
#   Nếu HTML/diagram đang nằm LẪN trong file khác (vd key `display` bên trong file YAML),
#   hãy TRÍCH XUẤT ra file riêng trước rồi mới render.

# ## ĐỌC ẢNH CÓ CROP (read_image / read_image_2)
# - Mọi ảnh (.png/.jpg/.jpeg/.gif/.webp) đều đọc bằng `read_image(file_path)` — KHÔNG đọc ảnh bằng `read_file`.
# - Ảnh được trả về ĐÚNG KÍCH THƯỚC GỐC (không resize, không giới hạn size) — muốn chi tiết hơn thì crop.
# - Hai tool crop cùng 1 vùng, khác nhau ở hệ tọa độ — chọn hệ nào tiện:
#   - `read_image(file_path, x1, y1, x2, y2)` — tọa độ PIXEL (tuyệt đối), gốc ở góc trái trên,
#     x2/y2 là cạnh phải/dưới KHÔNG chứa (box rộng x2-x1, cao y2-y1).
#   - `read_image_2(file_path, x1, y1, x2, y2)` — tọa độ SCALE 0-1000 (tương đối): x1/x2 đo chiều ngang,
#     y1/y2 đo chiều dọc, 0 = cạnh trái/trên, 1000 = cạnh phải/dưới. VD: 1/4 góc phải trên = 500, 0, 1000, 500.
#     Bắt buộc đủ 4 tọa độ (không có chế độ xem toàn ảnh — xem toàn ảnh dùng `read_image`).
# - Quy trình đọc ảnh 2 bước:
#   1. `read_image(file_path)` -> xem TOÀN ảnh. Kết quả kèm `image_width`/`image_height` (kích thước ảnh gốc, pixel).
#   2. Nếu cần nhìn sát 1 vùng (nét chữ nhỏ, 1 nhánh của sơ đồ, 1 bảng dữ liệu...), crop vùng đó bằng
#      `read_image` (pixel) hoặc `read_image_2` (scale 0-1000).
# - Ảnh render từ skill `render-to-image` có thể bị tách thành nhiều tile (`*.tile-NNN.png`) khi quá cao
#   -> đọc từng tile, và vẫn có thể crop trong từng tile bằng x1/y1/x2/y2.
# - Dùng ảnh để: đọc SQL diagram chuyển thành DML, phân tích lỗi từ screenshot, xem giao diện web, đọc sơ đồ mermaid, v.v.
# - File `.html`/`.mmd` cần render PHẢI là file riêng nằm trong workspace. Nếu HTML/diagram nằm LẪN trong file khác (vd key `display` trong YAML), hãy TRÍCH XUẤT ra file riêng trước rồi mới render.
