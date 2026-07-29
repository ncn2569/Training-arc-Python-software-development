import json
import sys
from pathlib import Path

path = sys.argv[1]

try:
    content = Path(path).read_text(encoding="utf-8")
    print(json.dumps({"success": True, "content": content}))
except Exception as e:
    print(json.dumps({"success": False, "content": str(e)}))
