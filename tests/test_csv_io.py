import csv
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from budget_app.models import Transaction
from budget_app.repository import TransactionRepository, CategoryStore, BudgetStore
from budget_app.csv_io import import_transactions, export_transactions


class TestCSVIO(unittest.TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = Path(self.temp_dir.name)
        self.repo = TransactionRepository(self.temp_dir.name)

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
        self.assertEqual(rows[0]["memo"], "점심")
        self.assertEqual(rows[0]["tags"], "meal")

    def test_export_rejects_storage_files(self):
        self.repo.save(Transaction(
            id="TX-001", date="2026-10-27", type="expense",
            category="food", amount=15000
        ))
        CategoryStore(self.temp_dir.name)
        BudgetStore(self.temp_dir.name).set("2026-10", 100000)
        for name in ("transactions.jsonl", "categories.jsonl", "budgets.jsonl"):
            with self.subTest(name=name):
                target = self.path / name
                original = target.read_bytes()

                with self.assertRaisesRegex(ValueError, "데이터 저장 파일에는"):
                    export_transactions(self.repo, str(target), month="2026-10")

                self.assertEqual(target.read_bytes(), original)
                self.assertEqual(list(self.path.glob(".*.tmp")), [])

    def test_export_failure_preserves_existing_output(self):
        output = self.path / "export.csv"
        original = b"previous export\n"
        output.write_bytes(original)

        def interrupted_load():
            yield Transaction(
                id="TX-001", date="2026-10-27", type="expense",
                category="food", amount=15000
            )
            raise OSError("simulated read failure")

        with patch.object(self.repo, "load", side_effect=interrupted_load):
            with self.assertRaises(OSError):
                export_transactions(self.repo, str(output), month="2026-10")

        self.assertEqual(output.read_bytes(), original)
        self.assertEqual(list(self.path.glob(".*.tmp")), [])

    def test_export_filters_month_and_inclusive_date_range(self):
        dates = ["2026-09-30", "2026-10-01", "2026-10-15", "2026-10-31", "2026-11-01"]
        for index, value in enumerate(dates, 1):
            self.repo.save(Transaction(
                id=f"TX-{index:03d}", date=value, type="expense",
                category="food", amount=1000
            ))
        cases = [
            ({"month": "2026-10"}, dates[1:4]),
            ({"date_from": "2026-10-15", "date_to": "2026-10-31"}, dates[2:4]),
        ]
        for filters, expected in cases:
            with self.subTest(filters=filters):
                output = self.path / "filtered.csv"
                count = export_transactions(self.repo, str(output), **filters)
                with output.open(encoding="utf-8", newline="") as source:
                    rows = list(csv.DictReader(source))
                self.assertEqual(count, len(expected))
                self.assertEqual([row["date"] for row in rows], expected)

    def test_export_import_round_trip(self):
        original = Transaction(
            id="TX-001", date="2026-10-27", type="expense", category="food",
            amount=15000, memo='점심, "식사"\n둘째 줄', tags=["식사", "친구"]
        )
        self.repo.save(original)
        output = self.path / "roundtrip.csv"
        self.assertEqual(export_transactions(self.repo, str(output), month="2026-10"), 1)
        destination = TransactionRepository(str(self.path / "imported"))
        self.assertEqual(import_transactions(destination, str(output), {"food"}), (1, 0))
        self.assertEqual(list(destination.load()), [original])

    def test_import_missing_header_preserves_transactions(self):
        self.repo.save(Transaction(
            id="TX-001", date="2026-10-27", type="expense",
            category="food", amount=15000
        ))
        original = self.repo.path.read_bytes()
        source = self.path / "missing-header.csv"
        source.write_text("date,type,category\n2026-10-27,expense,food\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "필수 컬럼"):
            import_transactions(self.repo, str(source), {"food"})
        self.assertEqual(self.repo.path.read_bytes(), original)

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
