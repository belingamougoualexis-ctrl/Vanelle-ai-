import tempfile
import unittest
from pathlib import Path

from worker import AgentError, Worker, safe_calculate


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "workspace"
        self.audit = Path(self.temp.name) / "audit.jsonl"
        self.worker = Worker(self.root, self.audit)

    def tearDown(self):
        self.temp.cleanup()

    def test_calculator_precedence_and_parentheses(self):
        self.assertEqual(safe_calculate("(12 + 3) * 4"), 60.0)

    def test_calculator_rejects_code(self):
        with self.assertRaises(AgentError):
            safe_calculate("__import__('os').system('whoami')")

    def test_write_requires_explicit_approval(self):
        result = self.worker.execute({"action": "workspace.write", "path": "hello.txt", "text": "hello"})
        self.assertEqual(result["status"], "approval_required")
        self.assertFalse((self.root / "hello.txt").exists())

    def test_approved_write_and_read(self):
        result = self.worker.execute({"action": "workspace.write", "path": "hello.txt", "text": "hello"}, approved=True)
        self.assertEqual(result["status"], "completed")
        read = self.worker.execute({"action": "workspace.read", "path": "hello.txt"})
        self.assertEqual(read["result"]["text"], "hello")

    def test_path_traversal_is_rejected(self):
        with self.assertRaises(AgentError):
            self.worker.execute({"action": "workspace.read", "path": "../../etc/passwd"})

    def test_unknown_action_is_rejected(self):
        with self.assertRaises(AgentError):
            self.worker.execute({"action": "shell.exec", "command": "whoami"})

    def test_system_info_and_audit(self):
        result = self.worker.execute({"action": "system.info"})
        self.assertEqual(result["status"], "completed")
        self.assertTrue(self.audit.exists())


if __name__ == "__main__":
    unittest.main()
