import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from budget_app.models import Transaction
from budget_app.repository import TransactionRepository
from budget_app.csv_io import import_transactions, export_transactions


class TestCSVIO(unittest.TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.path = Path(self.temp_dir.name)
        self.repo = TransactionRepository(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export(self):
        tx = Transaction(
            id="TX-001",
            date="2026-10-27",
            type="expense",
            category="food",
            amount=15000,
            memo="점심",
            tags=["meal"]
        )

        self.repo.save(tx)

        output = self.path / "export.csv"

        count = export_transactions(
            self.repo,
            out_file=str(output),
            month="2026-10"
        )

        with output.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))

        self.assertEqual(count, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["category"], "food")
        self.assertEqual(rows[0]["amount"], "15000")

    def test_import(self):
        input_file = self.path / "import.csv"

        input_file.write_text(
            "date,type,category,amount,memo,tags\n"
            "2026-10-27,expense,food,15000,점심,meal\n",
            encoding="utf-8"
        )

        imported, skipped = import_transactions(
            self.repo,
            csv_file=str(input_file),
            categories={"food"}
        )

        transactions = list(self.repo.load())

        self.assertEqual(imported, 1)
        self.assertEqual(skipped, 0)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].id, "TX-001")
        self.assertEqual(transactions[0].amount, 15000)

    def test_import_invalid_row(self):
        input_file = self.path / "invalid.csv"

        input_file.write_text(
            "date,type,category,amount,memo,tags\n"
            "2026-10-27,expense,food,15000,점심,meal\n"
            "2026-10-27,expense,food,abc,잘못된 금액,\n",
            encoding="utf-8"
        )

        imported, skipped = import_transactions(
            self.repo,
            csv_file=str(input_file),
            categories={"food"}
        )

        self.assertEqual(imported, 1)
        self.assertEqual(skipped, 1)
        self.assertEqual(len(list(self.repo.load())), 1)