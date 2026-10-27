"""Test TLS selection and recoverable environment replacement without downloads."""

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from task_completion_detector import environment


class TlsRequirementsTests(unittest.TestCase):
    """Run the isolated probe against controlled Python/SSL identities."""

    def test_supported_openssl_and_rejected_libressl_or_old_python(self) -> None:
        cases = (
            ("OpenSSL 1.1.1", (1, 1, 1), (3, 9), True),
            ("OpenSSL 3.0.0", (3, 0, 0), (3, 13), True),
            ("LibreSSL 2.8.3", (2, 8, 3), (3, 9), False),
            ("OpenSSL 1.0.2", (1, 0, 2), (3, 9), False),
            ("OpenSSL 3.0.0", (3, 0, 0), (3, 8), False),
        )
        for name, ssl_version, python_version, supported in cases:
            with self.subTest(name=name, python_version=python_version):
                prelude = (
                    "import sys, types; "
                    f"sys.version_info = {python_version!r}; "
                    "sys.modules['ssl'] = types.SimpleNamespace("
                    f"OPENSSL_VERSION={name!r}, OPENSSL_VERSION_INFO={ssl_version!r}); "
                )
                result = subprocess.run(
                    [sys.executable, "-I", "-c", prelude + environment._TLS_PROBE],
                    check=False,
                )
                self.assertEqual(result.returncode, 0 if supported else 1)

    def test_missing_interpreter_is_unsupported(self) -> None:
        self.assertFalse(environment._supports_tls(Path("/no/such/python")))


class InterpreterSelectionTests(unittest.TestCase):
    """Verify that explicit choices and fallback discovery remain predictable."""

    def test_explicit_interpreter_has_no_silent_fallback(self) -> None:
        with patch.dict(os.environ, {"TASK_WATCH_PYTHON": "/chosen/python"}):
            self.assertEqual(list(environment._python_candidates()), [Path("/chosen/python")])

    def test_path_discovery_includes_versioned_interpreters_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("python3", "python3.13", "python3-config"):
                (root / name).touch()
            with patch.dict(os.environ, {}, clear=True):
                with patch("os.get_exec_path", return_value=[directory, directory]):
                    candidates = list(environment._python_candidates())
            self.assertEqual(candidates.count(root / "python3"), 1)
            self.assertIn(root / "python3.13", candidates)
            self.assertNotIn(root / "python3-config", candidates)

    def test_selection_skips_own_environment_and_incompatible_python(self) -> None:
        venv = Path("/project/python/.venv")
        with patch.object(environment, "_python_candidates", return_value=iter([
            venv / "bin/python3", Path("/system/python3"), Path("/compatible/python3"),
        ])):
            with patch.object(environment, "_supports_tls", side_effect=[False, True]):
                self.assertEqual(environment._select_python(venv), Path("/compatible/python3"))


class EnvironmentLifecycleTests(unittest.TestCase):
    """Keep failed migrations reversible and preserve private configuration."""

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.venv = self.root / "python/.venv"
        (self.venv / "bin").mkdir(parents=True)
        (self.venv / "bin/python").touch()
        (self.venv / "original").write_text("old environment", encoding="utf-8")
        (self.root / "config").mkdir()
        self.config = self.root / "config/config.txt"
        self.config.write_text("private local configuration", encoding="utf-8")
        for patcher in (
            patch.object(environment, "_supports_tls", return_value=False),
            patch.object(environment, "_select_python", return_value=Path("/compatible/python3")),
            patch.dict(os.environ, {"LANGUAGE": "en"}),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        for redirect in (
            contextlib.redirect_stdout(self.stdout),
            contextlib.redirect_stderr(self.stderr),
        ):
            redirect.__enter__()
            self.addCleanup(redirect.__exit__, None, None, None)

    def _create_replacement(self, *_args, **_kwargs) -> None:
        """Simulate venv creation without executing a real interpreter."""
        (self.venv / "bin").mkdir(parents=True)
        (self.venv / "bin/python").touch()
        (self.venv / "replacement").touch()

    def test_successful_migration_retains_backup_and_configuration(self) -> None:
        with patch.object(environment.subprocess, "run", side_effect=self._create_replacement):
            with patch.object(environment, "_install_requirements"):
                environment.bootstrap_environment(self.root)
        backups = list(self.venv.parent.glob(".venv-backup-*"))
        self.assertEqual(len(backups), 1)
        self.assertTrue((backups[0] / "original").exists())
        self.assertTrue((self.venv / "replacement").exists())
        self.assertIn(str(backups[0]), self.stdout.getvalue())
        self.assertEqual(self.config.read_text(encoding="utf-8"), "private local configuration")

    def test_dependency_failure_restores_original_environment(self) -> None:
        with patch.object(environment.subprocess, "run", side_effect=self._create_replacement):
            with patch.object(environment, "_install_requirements", side_effect=subprocess.CalledProcessError(1, "pip")):
                with self.assertRaises(subprocess.CalledProcessError):
                    environment.bootstrap_environment(self.root)
        self.assertTrue((self.venv / "original").exists())
        self.assertFalse((self.venv / "replacement").exists())
        self.assertEqual(list(self.venv.parent.glob(".venv-backup-*")), [])
        self.assertIn("restored", self.stderr.getvalue())
        self.assertEqual(self.config.read_text(encoding="utf-8"), "private local configuration")

    def test_interrupted_migration_restores_original_environment(self) -> None:
        with patch.object(environment.subprocess, "run", side_effect=self._create_replacement):
            with patch.object(environment, "_install_requirements", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    environment.bootstrap_environment(self.root)
        self.assertTrue((self.venv / "original").exists())

    def test_creation_failure_restores_original_environment(self) -> None:
        with patch.object(environment.subprocess, "run", side_effect=OSError("creation failed")):
            with self.assertRaises(OSError):
                environment.bootstrap_environment(self.root)
        self.assertTrue((self.venv / "original").exists())

    def test_missing_compatible_python_leaves_existing_environment_intact(self) -> None:
        with patch.object(environment, "_select_python", side_effect=environment.PythonUnavailableError):
            with self.assertRaises(environment.PythonUnavailableError):
                environment.bootstrap_environment(self.root)
        self.assertTrue((self.venv / "original").exists())
        self.assertEqual(list(self.venv.parent.glob(".venv-backup-*")), [])

    def test_healthy_environment_is_reused(self) -> None:
        with patch.object(environment, "_supports_tls", return_value=True):
            with patch.object(environment, "_install_requirements"):
                environment.bootstrap_environment(self.root)
        self.assertTrue((self.venv / "original").exists())
        self.assertEqual(list(self.venv.parent.glob(".venv-backup-*")), [])


class PipInvocationTests(unittest.TestCase):
    """Ensure setup upgrades pip within the chosen environment only."""

    def test_pip_is_bound_to_environment_and_dependencies_are_not_upgraded(self) -> None:
        with patch.object(environment.subprocess, "run") as run:
            environment._install_requirements(Path("/env/bin/python"), Path("/project/requirements.txt"), True)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(len(commands), 2)
        self.assertTrue(all(command[:4] == ["/env/bin/python", "-I", "-m", "pip"] for command in commands))
        self.assertEqual(commands[0][-2:], ["--upgrade", "pip"])
        self.assertEqual(commands[1][-2:], ["-r", "/project/requirements.txt"])
        self.assertNotIn("--upgrade", commands[1])


if __name__ == "__main__":
    unittest.main()
