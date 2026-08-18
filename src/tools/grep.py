import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess

from tools.path import BASHPATH, WORKSPACE, resolve_path


def grep_search(
    pattern: str,
    path: str,
    glob: str | None = None,
    output_mode: str = "files_with_matches",
    context: int | None = None,
) -> dict:
    """
    output_mode 1 trong 3:
    files_with_matches : file paths only, no line content. This is the default.
    content :  matching lines with file and line number.
    count : match count per file, followed by a total across all matching files.
    """
    try:
        file_path = resolve_path(path)
        grep_command = ["grep", "--color=never", "-n", "-r", "-H"]

        if output_mode == "files_with_matches":
            grep_command.append("-l")
        elif output_mode == "count":
            grep_command.append("-c")
        else:
            if context is not None:
                grep_command.extend(["-C", str(context)])

        if glob and glob != "":
            grep_command.append(f"--include={glob}")

        grep_command.append(f"'{pattern}'")
        grep_command.append(str(file_path).replace("\\", "/"))
        grep_command = " ".join(grep_command)

        result = subprocess.run(
            [BASHPATH, "-c", grep_command],
            shell=True,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode == 1:
            return {
                "success": True,
                "pattern": pattern,
                "path": path,
                "glob": glob,
                "output_mode": output_mode,
                "matches": [],
                "total_matches": 0,
            }
        elif result.returncode >= 2:
            return {
                "success": False,
                "pattern": pattern,
                "path": path,
                "error": stderr or f"grep exited with code {result.returncode}",
            }
        else:  # retun code == 0
            if output_mode == "files_with_matches":
                matches = stdout.split("\n") if stdout else []

                return {
                    "success": True,
                    "pattern": pattern,
                    "path": path,
                    "glob": glob,
                    "output_mode": output_mode,
                    "matches": matches,
                    "total_matches": len(matches),
                }
            elif output_mode == "count":
                lines = stdout.split("\n") if stdout else []

                match_list = []
                total = 0

                for line in lines:
                    if ":" in line:
                        file_part, _, count_part = line.rpartition(":")
                        try:
                            c = int(count_part)
                            match_list.append({"file": file_part, "count": c})
                            total += c
                        except Exception as e:
                            match_list.append({"file": line, "error": str(e), "count": 0})
                return {
                    "success": True,
                    "pattern": pattern,
                    "path": path,
                    "glob": glob,
                    "output_mode": output_mode,
                    "matches": match_list,
                    "total_matches": total,
                }
            else:
                lines = stdout.split("\n") if stdout else []
                match_list = []
                for line in lines:
                    if line == "--":
                        continue

                    # Tìm vị trí chữ số đầu tiên -> kí tự ngay trước nó là separator
                    first_digit_idx = -1
                    for i, ch in enumerate(line):
                        if ch.isdigit():
                            first_digit_idx = i
                            break
                    
                    # định dạng không đọc được thì grep trả về binary files matches
                    if first_digit_idx <= 0:
                        match_list.append({"raw": line})
                        continue

                    sep = line[first_digit_idx - 1]  # ':' = match, '-' = context
                    file_part = line[: first_digit_idx - 1]
                    rest = line[first_digit_idx:]  # "42:def foo()" hoặc "40- x = 1"
                    second_sep_idx = rest.find(sep)
                    line_num = int(rest[:second_sep_idx])
                    content = rest[second_sep_idx + 1 :]
                    match_list.append(
                        {
                            "file": file_part,
                            "line": line_num,
                            "content": content,
                            "type": "match" if sep == ":" else "context",
                        }
                    )
            return {
                "success": True,
                "pattern": pattern,
                "path": path,
                "glob": glob,
                "output_mode": output_mode,
                "matches": match_list,
                "total_matches": len(match_list),
            }
    except Exception as e:
        return {"success": False, "pattern": pattern, "path": path, "error": str(e)}


if __name__ == "__main__":
    print(
        grep_search(
            path="base.js",
            pattern="Bsn = class extends",
            output_mode="content",
        )
    )

#grep --color=never -n -r -H -C 3 "var Bsn = class extends Tq" workspace/base.js

# {
#     "success": True,
#     "pattern": "Bsn = class extends",
#     "path": "base.js",
#     "glob": None,
#     "output_mode": "content",
#     "matches": [
#         {
#             "file": "D:/Inter-K/workspace/base.js",
#             "line": 18976,
#             "content": "         this.B.forEach(r => { r.hide() });",
#             "type": "context",
#         },
#         {
#             "file": "D:/Inter-K/workspace/base.js",
#             "line": 18977,
#             "content": "         super.hide()",
#             "type": "context",
#         },
#         {
#             "file": "D:/Inter-K/workspace/base.js",
#             "line": 18978,
#             "content": "      }",
#             "type": "context",
#         },
#         {
#             "file": "D:/Inter-K/workspace/base.js",
#             "line": 18979,
#             "content": "   }; var Bsn = class extends Tq {",
#             "type": "match",
#         },
#         {
#             "file": "D:/Inter-K/workspace/base.js",
#             "line": 18980,
#             "content": '      constructor(r, z, P, h) { super(r, { N: "div", C: "ytp-image-background", Y: [{ N: "img", C: "ytp-image-background-image" }] }, "image-background", z, P, h); this.hide() } init(r, z) {',
#             "type": "context",
#         },
#         {
#             "file": "D:/Inter-K/workspace/base.js",
#             "line": 18981,
#             "content": '         super.init(r, z, {}); if ((r = ho(z.image?.sources || [])?.url || "") && r.length) {',
#             "type": "context",
#         },
#         {
#             "file": "D:/Inter-K/workspace/base.js",
#             "line": 18982,
#             "content": '            var P = this.sS("ytp-image-background-image"); g.g8(P, "backgroundImage", `url(${r})`); z.blurLevel !== void 0 && g.g8(P, "filter", `blur(${z.blurLevel}px)`); z.gradient !== void 0 && (z = new g.Q({ N: "div", hU: ["ytp-image-background--gradient-vertical"] }), g.S(this, z),',
#             "type": "context",
#         },
#     ],
#     "total_matches": 7,
# }
