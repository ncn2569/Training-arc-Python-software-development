import os
import subprocess
import time

from tools.path import BASHPATH, VENVSCRIPTS, WORKSPACE


def run_shell(command: str) -> dict:

    env = os.environ.copy()

    if VENVSCRIPTS.exists():
        # Đưa venv/Scripts lên ĐẦU biến PATH
        env["PATH"] = f"{VENVSCRIPTS};{env.get('PATH', '')}"
        env["VIRTUAL_ENV"] = str(VENVSCRIPTS.parent)

    try:
        result = subprocess.run(
            [BASHPATH, "-c", command],
            shell=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=WORKSPACE,
            timeout=300,
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
