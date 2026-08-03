import json
import os
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path("./workspace").resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)


ROOT_DIR = Path(__file__).parent.parent.resolve()
VENV_SCRIPTS = ROOT_DIR / "venv" / "Scripts"

BASH_PATH = r"D:\git\Git\bin\bash.exe"


def run_shell(command: str) -> dict:

    env = os.environ.copy()
    
    if VENV_SCRIPTS.exists():
        # Đưa venv/Scripts lên ĐẦU biến PATH
        env["PATH"] = f"{VENV_SCRIPTS};{env.get('PATH', '')}"
        env["VIRTUAL_ENV"] = str(VENV_SCRIPTS.parent)

    try:
        result = subprocess.run(
            [BASH_PATH, "-c", command],
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=WORKSPACE,
            timeout=120,
            env=env
        )
        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "cwd": str(WORKSPACE),
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "COMMAND_TIMEOUT"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# if __name__ == "__main__":
#     input = json.loads(sys.stdin.read())

#     print(json.dumps(run_shell(input["command"])))
