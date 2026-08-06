import os
import subprocess
import time

from tools.path import BASH_PATH, VENV_SCRIPTS, WORKSPACE


def run_shell(command: str) -> dict:

    env = os.environ.copy()

    if VENV_SCRIPTS.exists():
        # Đưa venv/Scripts lên ĐẦU biến PATH
        env["PATH"] = f"{VENV_SCRIPTS};{env.get('PATH', '')}"
        env["VIRTUAL_ENV"] = str(VENV_SCRIPTS.parent)

    try:
        # print("RUNNING SHELL...")
        # time.sleep(3)
        result = subprocess.run(
            [BASH_PATH, "-c", command],
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=WORKSPACE,
            timeout=120,
            env=env,
        )
        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "cwd": str(WORKSPACE),
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "COMMAND_TIMEOUT"}
    except Exception as e:
        return {"success": False, "error": str(e)}
