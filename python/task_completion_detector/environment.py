"""Prepare the Unix launchers' virtual environment using an OpenSSL Python.

This module uses only the standard library and localization resources, so the
system Python can run it before application dependencies are installed. Failed
replacements restore the original environment; successful replacements retain
a backup alongside .venv. Configuration lives outside these directories.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Iterator, Optional

from .i18n import translate

_TLS_PROBE = (
    "import ssl, sys; sys.exit(0 if sys.version_info >= (3, 9) "
    "and ssl.OPENSSL_VERSION.startswith('OpenSSL ') "
    "and ssl.OPENSSL_VERSION_INFO >= (1, 1, 1) else 1)"
)


class PythonUnavailableError(RuntimeError):
    """Indicate that no interpreter meets the application's TLS requirements."""


def _supports_tls(python: Path) -> bool:
    """Probe an interpreter in isolation without importing application packages."""
    try:
        result = subprocess.run(
            [str(python), "-I", "-c", _TLS_PROBE],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _python_candidates() -> Iterator[Path]:
    """Find Python executables on PATH and common macOS installation paths.

    TASK_WATCH_PYTHON selects one explicit executable when creating or replacing
    an environment. Common paths also support Finder's restricted PATH.
    """
    override = os.environ.get("TASK_WATCH_PYTHON")
    if override:
        yield Path(shutil.which(override) or override).expanduser().absolute()
        return

    directories = os.get_exec_path() + [
        "/opt/homebrew/bin",
        "/usr/local/bin",
        "/Library/Frameworks/Python.framework/Versions/Current/bin",
        "/usr/bin",
    ]
    seen = set()
    for directory in directories:
        for candidate in sorted(
            Path(directory).glob("python3*"),
            key=lambda item: (item.name != "python3", item.name),
        ):
            if re.fullmatch(r"python3(?:\.\d+)?", candidate.name):
                candidate = candidate.absolute()
                if candidate not in seen:
                    seen.add(candidate)
                    yield candidate


def _select_python(venv: Path) -> Path:
    """Find a compatible interpreter outside the environment being replaced."""
    for candidate in _python_candidates():
        if venv not in candidate.parents and _supports_tls(candidate):
            return candidate
    raise PythonUnavailableError()


def _install_requirements(python: Path, requirements: Path, refresh: bool) -> None:
    """Install through the environment's pip, refreshing pip on setup/update."""
    command = [str(python), "-I", "-m", "pip", "--disable-pip-version-check", "install", "--quiet"]
    if refresh:
        subprocess.run(command + ["--upgrade", "pip"], check=True)
    subprocess.run(command + ["-r", str(requirements)], check=True)


def bootstrap_environment(project_root: Path, refresh: bool = False) -> None:
    """Create or reuse an OpenSSL environment, restoring backups on failure.

    Only python/.venv and its backups are changed. A compatible existing
    environment is reused. An incompatible environment is moved aside only
    after a replacement interpreter has been found. Setup and update refresh
    pip; dependency constraints remain owned by requirements.txt.
    """
    venv = project_root / "python" / ".venv"
    python = venv / "bin" / "python"
    requirements = project_root / "requirements.txt"
    if python.exists() and _supports_tls(python):
        _install_requirements(python, requirements, refresh)
        return

    selected = _select_python(venv)
    print(translate("environment.preparing", python=str(selected)), flush=True)
    backup: Optional[Path] = None
    if venv.exists():
        backup = venv.with_name(".venv-backup-" + uuid.uuid4().hex[:12])
        venv.rename(backup)

    try:
        subprocess.run([str(selected), "-I", "-m", "venv", str(venv)], check=True)
        _install_requirements(python, requirements, refresh=True)
    except (OSError, subprocess.SubprocessError, KeyboardInterrupt):
        if venv.exists():
            shutil.rmtree(venv)
        if backup is not None:
            backup.rename(venv)
            print(translate("environment.restored"), file=sys.stderr)
        raise

    if backup is not None:
        print(translate("environment.backup", backup=str(backup)))


def main() -> None:
    """Prepare the checkout's environment; return nonzero with localized errors."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    try:
        bootstrap_environment(Path(__file__).resolve().parents[2], args.refresh)
    except PythonUnavailableError:
        print(translate("environment.python_required"), file=sys.stderr)
        raise SystemExit(1) from None
    except (OSError, subprocess.SubprocessError):
        print(translate("environment.failed"), file=sys.stderr)
        raise SystemExit(1) from None
    except KeyboardInterrupt:
        raise SystemExit(130) from None


if __name__ == "__main__":
    main()
