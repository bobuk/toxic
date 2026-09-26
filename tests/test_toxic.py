import contextlib
import importlib.machinery
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


TOXIC_PATH = Path(__file__).resolve().parents[1] / "toxic"
loader = importlib.machinery.SourceFileLoader("toxic_cli", str(TOXIC_PATH))
spec = importlib.util.spec_from_loader(loader.name, loader)
toxic = importlib.util.module_from_spec(spec)
loader.exec_module(toxic)


def session(name, root):
    return {
        "name": name,
        "identifier": f"{name}-id",
        "status": "watching",
        "mode": "two-way-safe",
        "successfulCycles": 3,
        "alpha": {
            "protocol": "local",
            "path": str(root),
            "directories": 2,
            "files": 4,
            "totalFileSize": 1024,
        },
        "beta": {"protocol": "ssh", "host": "example.test", "path": "/srv/project"},
    }


class GuiCommandTests(unittest.TestCase):
    def test_gui_materializes_embedded_swift_app_and_forwards_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            completed = toxic.subprocess.CompletedProcess(["swift"], 0)
            with (
                mock.patch.object(toxic.sys, "platform", "darwin"),
                mock.patch.object(toxic.tempfile, "gettempdir", return_value=tmp),
                mock.patch.object(toxic.subprocess, "run", return_value=completed) as run,
            ):
                result = toxic.cmd_gui(["."])

            gui_path = Path(tmp) / "toxic-gui.swift"
            self.assertEqual(gui_path.read_text(), toxic.TOXIC_GUI_SOURCE)
            run.assert_called_once_with(["swift", str(gui_path), "."])

        self.assertEqual(result, 0)

    def test_gui_help_does_not_launch_swift(self):
        output = io.StringIO()
        with mock.patch.object(toxic.subprocess, "run") as run, contextlib.redirect_stdout(output):
            result = toxic.cmd_gui(["--help"])

        self.assertEqual(result, 0)
        self.assertIn("usage: toxic gui [path]", output.getvalue())
        run.assert_not_called()

    def test_gui_is_rejected_outside_macos(self):
        errors = io.StringIO()
        with (
            mock.patch.object(toxic.sys, "platform", "linux"),
            contextlib.redirect_stderr(errors),
            self.assertRaises(SystemExit) as raised,
        ):
            toxic.cmd_gui([])

        self.assertEqual(raised.exception.code, 1)
        self.assertIn("available only on macOS", errors.getvalue())

    def test_embedded_gui_registers_standard_quit_shortcut(self):
        self.assertIn('keyEquivalent: "q"', toxic.TOXIC_GUI_SOURCE)
        self.assertIn("quitItem.keyEquivalentModifierMask = .command", toxic.TOXIC_GUI_SOURCE)
        self.assertIn("quitItem.target = NSApp", toxic.TOXIC_GUI_SOURCE)

    def test_embedded_gui_uses_compact_binary_status_indicator(self):
        self.assertIn('textField.stringValue = "●"', toxic.TOXIC_GUI_SOURCE)
        self.assertIn("session.needsAttention ? .systemRed : .systemGreen", toxic.TOXIC_GUI_SOURCE)
        self.assertNotIn('"●  " + session.displayStatus', toxic.TOXIC_GUI_SOURCE)
        self.assertIn("tableView.rowHeight = 24", toxic.TOXIC_GUI_SOURCE)


class PathStatusTests(unittest.TestCase):
    def test_path_status_uses_most_specific_covering_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            outer = Path(tmp)
            project = outer / "project"
            child = project / "src"
            child.mkdir(parents=True)
            sessions = [session("outer", outer), session("project", project)]

            output = io.StringIO()
            with mock.patch.object(toxic, "sessions", return_value=sessions), contextlib.redirect_stdout(output):
                result = toxic.cmd_path_status(str(child))

        self.assertEqual(result, 0)
        self.assertIn("project  watching", output.getvalue())
        self.assertNotIn("outer  watching", output.getvalue())

    def test_path_status_reports_when_no_session_covers_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = io.StringIO()
            with mock.patch.object(toxic, "sessions", return_value=[]), contextlib.redirect_stdout(output):
                result = toxic.cmd_path_status(tmp)

        self.assertEqual(result, 1)
        self.assertIn("no sync session covers", output.getvalue())

    def test_main_dispatches_dot_as_a_path(self):
        with mock.patch.object(toxic, "cmd_path_status", return_value=0) as path_status:
            result = toxic.main(["."])

        self.assertEqual(result, 0)
        path_status.assert_called_once_with(".")

    def test_main_dispatches_existing_bare_directory_as_a_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            project.mkdir()
            old_cwd = os.getcwd()
            try:
                os.chdir(tmp)
                with mock.patch.object(toxic, "cmd_path_status", return_value=0) as path_status:
                    result = toxic.main(["project"])
            finally:
                os.chdir(old_cwd)

        self.assertEqual(result, 0)
        path_status.assert_called_once_with("project")


class DoctorTests(unittest.TestCase):
    def test_doctor_issues_collects_conflicts_problems_and_halts(self):
        s = session("web", "/tmp/web")
        s["conflicts"] = [{"root": "src/a.py"}]
        s["alpha"]["scanProblems"] = [{"path": "b", "error": "permission denied"}]
        s["beta"]["excludedScanProblems"] = 2
        s["status"] = "halted-on-root-emptied"
        kinds = [k for k, _ in toxic.doctor_issues(s)]
        self.assertEqual(kinds, ["conflict", "problem", "excluded", "halted"])

    def test_paused_sessions_skip_connectivity_issues(self):
        s = session("web", "/tmp/web")
        s["paused"] = True
        s["status"] = "disconnected"
        s["alpha"]["connected"] = False
        self.assertEqual(toxic.doctor_issues(s), [])

    def test_unconnected_endpoint_is_an_issue(self):
        s = session("web", "/tmp/web")
        s["beta"]["connected"] = False
        self.assertEqual(toxic.doctor_issues(s), [("offline", "beta not connected")])

    def test_doctor_reports_all_healthy(self):
        output = io.StringIO()
        with (
            mock.patch.object(toxic, "sessions", return_value=[session("a", "/tmp/a")]),
            contextlib.redirect_stdout(output),
        ):
            result = toxic.cmd_doctor([])
        self.assertEqual(result, 0)
        self.assertIn("all healthy", output.getvalue())

    def test_doctor_lists_issues_without_a_tty(self):
        s = session("web", "/tmp/web")
        s["conflicts"] = [{"root": "x", "alphaChanges": [{"new": {"kind": "file"}}], "betaChanges": []}]
        output = io.StringIO()
        with (
            mock.patch.object(toxic, "sessions", return_value=[s]),
            contextlib.redirect_stdout(output),
        ):
            result = toxic.cmd_doctor(["--dry-run"])
        self.assertEqual(result, 1)
        out = output.getvalue()
        self.assertIn("1 issue in 1 of 1 sessions", out)
        self.assertIn("conflict", out)
        self.assertIn("x", out)


if __name__ == "__main__":
    unittest.main()
