import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("audit-design-rules.py").resolve()


class AuditCommandTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="design audit ")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def run_audit(self, target):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), str(target)],
            cwd=self.root,
            capture_output=True,
            text=True,
        )

    def test_missing_target_is_an_error(self):
        result = self.run_audit(self.root / "missing")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("均合规", result.stdout)

    def test_directory_without_supported_files_is_an_error(self):
        (self.root / "notes.md").write_text("No frontend source", encoding="utf-8")
        result = self.run_audit(self.root)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("均合规", result.stdout)

    def test_clean_source_passes_from_another_working_directory(self):
        (self.root / "page.tsx").write_text("export default () => <main />;", encoding="utf-8")
        result = self.run_audit(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("均合规", result.stdout)

    def test_violation_returns_failure(self):
        target = self.root / "page.tsx"
        target.write_text('<div className="border-black" />', encoding="utf-8")
        result = self.run_audit(target)
        self.assertEqual(result.returncode, 1)
        self.assertIn("DS-001", result.stdout)

    def test_read_failure_is_reported_without_a_traceback(self):
        target = self.root / "invalid.tsx"
        target.write_bytes(b"\xff")
        result = self.run_audit(target)
        self.assertEqual(result.returncode, 1)
        self.assertIn("IO-ERR", result.stdout)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
