import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from budget_app.models import Transaction
from budget_app.repository import TransactionRepository


class TestCLI(unittest.TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.root = Path(__file__).resolve().parents[1]

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, *args, input_text=None):
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "budget_app",
                "--data-dir",
                self.temp_dir.name,
                *args,
            ],
            cwd=self.root,
            input=input_text,
            capture_output=True,
            text=True,
        )

    def test_help(self):
        result = self.run_cli("--help")

        self.assertEqual(result.returncode, 0)
        self.assertIn("usage:", result.stdout)

    def test_invalid_limit(self):
        result = self.run_cli("list", "--limit", "0")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--limit", result.stdout + result.stderr)

    def test_budget_set_and_summary(self):
        result = self.run_cli(
            "budget", "set",
            "--month", "2026-10",
            "--amount", "100000"
        )

        self.assertEqual(result.returncode, 0)

        result = self.run_cli(
            "summary", "--month", "2026-10"
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("100000원", result.stdout)

    def test_remove_used_category(self):
        repo = TransactionRepository(self.temp_dir.name)

        repo.save(Transaction(
            id="TX-001",
            date="2026-10-27",
            type="expense",
            category="food",
            amount=15000
        ))

        result = self.run_cli(
            "category", "remove",
            input_text="food\n"
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "사용 중인 카테고리",
            result.stdout + result.stderr
        )