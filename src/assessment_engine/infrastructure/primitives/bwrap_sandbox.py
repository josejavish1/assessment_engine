import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass

@dataclass
class BwrapExecutionResult:
    exit_code: int
    stdout: str
    stderr: str
    sandboxed: bool

class BubblewrapSandboxRunner:
    def __init__(self):
        self.binary = shutil.which("bwrap")

    def is_available(self) -> bool:
        """Check whether the resource is available."""
        return self.binary is not None

    def execute_jailed_command(
        self,
        workspace_dir: Path,
        command: list[str],
        allow_network: bool = False
    ) -> BwrapExecutionResult:
        """Execute a command within a jailed environment."""
        if not self.is_available():
            # Fall back safely without a sandbox if bwrap is not installed.
            res = subprocess.run(command, cwd=workspace_dir, capture_output=True, text=True)
            return BwrapExecutionResult(res.returncode, res.stdout, res.stderr, False)

        bwrap_args = [
            self.binary,
            "--ro-bind", "/", "/",
            "--dev", "/dev",
            "--proc", "/proc",
            "--tmpfs", "/tmp",
            "--bind", str(workspace_dir.resolve()), str(workspace_dir.resolve()),
            "--chdir", str(workspace_dir.resolve())
        ]
        if not allow_network:
            bwrap_args.append("--unshare-net")

        full_cmd = bwrap_args + command
        res = subprocess.run(full_cmd, capture_output=True, text=True)
        return BwrapExecutionResult(res.returncode, res.stdout, res.stderr, True)


bwrap_sandbox = BubblewrapSandboxRunner()

