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
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(__file__).resolve().parents[1]

    def run_cli(self, *args, input_text=None):
        return subprocess.run(
            [
                sys.executable,
                "-B",
                "-X", "utf8",
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
            encoding="utf-8",
            timeout=15,
        )

    def test_help(self):
        commands = [
            (), ("add",), ("list",), ("search",), ("summary",),
            ("update",), ("delete",), ("import",), ("export",),
            ("category",), ("category", "add"), ("category", "list"),
            ("category", "remove"), ("budget",), ("budget", "set"),
        ]
        for command in commands:
            with self.subTest(command=command):
                result = self.run_cli(*command, "--help")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout)

    def test_add_update_delete_across_processes(self):
        result = self.run_cli(
            "add", input_text="2026-10-27\nexpense\nfood\n15000\n점심\n식사,친구\n"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        repo = TransactionRepository(self.temp_dir.name)
        transactions = list(repo.load())
        self.assertEqual(len(transactions), 1)
        tx = transactions[0]
        self.assertIn(tx.id, result.stdout)
        self.assertEqual(tx.memo, "점심")
        self.assertEqual(tx.tags, ["식사", "친구"])

        result = self.run_cli("list")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(tx.id, result.stdout)
        result = self.run_cli("update", "--id", tx.id, "--amount", "20000")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list(repo.load())[0].amount, 20000)
        result = self.run_cli("delete", "--id", tx.id)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list(repo.load()), [])

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
        self.assertIn("데이터 없음", result.stdout)

    def test_malformed_csv_reports_error_and_preserves_transactions(self):
        repo = TransactionRepository(self.temp_dir.name)
        repo.save(Transaction(
            id="TX-001", date="2026-10-27", type="expense",
            category="food", amount=15000
        ))
        original = repo.path.read_bytes()
        source = Path(self.temp_dir.name) / "broken.csv"
        source.write_text(
            "date,type,category,amount,memo,tags\n"
            "2026-10-27,expense,food,1000,valid,\n"
            '2026-10-27,expense,food,2000,"unclosed\n',
            encoding="utf-8"
        )

        result = self.run_cli("import", "--from", str(source))
        messages = result.stdout + result.stderr

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("[오류]", messages)
        self.assertIn("[힌트]", messages)
        self.assertNotIn("Traceback", messages)
        self.assertEqual(repo.path.read_bytes(), original)
        self.assertEqual(list(Path(self.temp_dir.name).glob(".*.tmp")), [])

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
