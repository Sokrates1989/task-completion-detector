"""Exercise Unix launcher setup and update routing in disposable checkouts."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(shutil.which("zsh"), "Unix launchers require zsh")
class LauncherSetupTests(unittest.TestCase):
    """Replace application and Git boundaries so tests cannot access the desktop."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        source = Path(__file__).resolve().parents[2]
        for relative in (
            "task-watch.sh",
            "setup/modules/task-watch-helpers.sh",
            "launchers/ai-select.sh",
            "launchers/ai-watch.sh",
            "launchers/ai-select.command",
            "launchers/ai-watch.command",
        ):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / relative, destination)
        package = self.root / "python/task_completion_detector"
        package.mkdir(parents=True)
        (package / "__init__.py").touch()
        self.bootstrap = package / "environment.py"
        self.bootstrap.write_text("", encoding="utf-8")
        venv = self.root / "python/.venv/bin"
        venv.mkdir(parents=True)
        (venv / "python").symlink_to(sys.executable)
        (venv / "activate").write_text(
            'export PATH="${PROJECT_ROOT}/python/.venv/bin:${PATH}"\n', encoding="utf-8"
        )
        (self.root / "python/main.py").write_text(
            "import json, sys\nfrom pathlib import Path\n"
            "with Path('calls.jsonl').open('a') as stream:\n"
            "    stream.write(json.dumps(sys.argv[1:]) + '\\n')\n",
            encoding="utf-8",
        )

    def _run(self, launcher: str, *args: str, env=None) -> subprocess.CompletedProcess:
        """Invoke a launcher with isolated environment variables and no network."""
        clean_environment = os.environ.copy()
        for variable in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
            clean_environment.pop(variable, None)
        clean_environment.update(env or {})
        return subprocess.run(
            [shutil.which("zsh"), str(self.root / launcher), *args],
            env=clean_environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_failed_setup_does_not_launch_monitor_or_selector(self) -> None:
        self.bootstrap.write_text("raise SystemExit(23)\n", encoding="utf-8")
        result = self._run("task-watch.sh", "--select-region")
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertFalse((self.root / "python/calls.jsonl").exists())

    def test_legacy_launchers_preserve_selection_and_monitoring_modes(self) -> None:
        cases = (
            ("launchers/ai-select.command", [["select-region", "--name", "default"]]),
            ("launchers/ai-watch.command", [["monitor", "--name", "default"]]),
            ("launchers/ai-select.sh", [
                ["select-region", "--name", "default"], ["monitor", "--name", "default"],
            ]),
            ("launchers/ai-watch.sh", [["monitor", "--name", "default"]]),
        )
        calls = self.root / "python/calls.jsonl"
        for launcher, expected in cases:
            with self.subTest(launcher=launcher):
                if calls.exists():
                    calls.unlink()
                result = self._run(launcher)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual([json.loads(line) for line in calls.read_text().splitlines()], expected)

    def test_update_reloads_pulled_bootstrap_before_refresh(self) -> None:
        (self.root / ".git").mkdir()
        updated = self.root / "updated-helpers.sh"
        updated.write_text(
            'bootstrap_python_env() { printf "%s" "$*" > "${PROJECT_ROOT}/refresh-args"; }\n'
            'migrate_screenshot_config() { touch "${PROJECT_ROOT}/migration-ran"; }\n',
            encoding="utf-8",
        )
        fake_bin = self.root / "fake-bin"
        fake_bin.mkdir()
        git = fake_bin / "git"
        git.write_text(
            '#!/bin/sh\ncp "$UPDATED_HELPERS" "$PROJECT_ROOT/setup/modules/task-watch-helpers.sh"\n',
            encoding="utf-8",
        )
        git.chmod(0o755)
        result = self._run("task-watch.sh", "--update", env={
            "PROJECT_ROOT": str(self.root),
            "UPDATED_HELPERS": str(updated),
            "PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", ""),
        })
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.root / "refresh-args").read_text(), "--refresh")
        self.assertTrue((self.root / "migration-ran").exists())


if __name__ == "__main__":
    unittest.main()
