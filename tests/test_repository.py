import unittest
from dataclasses import replace
from tempfile import TemporaryDirectory

from budget_app.models import Transaction
from budget_app.repository import TransactionRepository


class TestTransactionRepository(unittest.TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.repo = TransactionRepository(self.temp_dir.name)

        self.tx = Transaction(
            id="TX-001",
            date="2026-10-27",
            type="expense",
            category="food",
            amount=15000
        )

    def test_save_and_load(self):
        self.repo.save(self.tx)

        reopened = TransactionRepository(self.temp_dir.name)
        transactions = list(reopened.load())

        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0], self.tx)

    def test_update(self):
        self.repo.save(self.tx)
        other = replace(self.tx, id="TX-002", amount=3000)
        self.repo.save(other)

        result = self.repo.update(
            "TX-001",
            {"amount": 20000}
        )

        self.assertTrue(result)
        self.assertEqual(list(self.repo.load()), [replace(self.tx, amount=20000), other])

    def test_delete(self):
        self.repo.save(self.tx)
        other = replace(self.tx, id="TX-002")
        self.repo.save(other)

        result = self.repo.delete("TX-001")

        self.assertTrue(result)
        self.assertEqual(list(self.repo.load()), [other])

    def test_duplicate_id(self):
        self.repo.save(self.tx)

        with self.assertRaises(ValueError):
            self.repo.save(self.tx)
        self.assertEqual(list(self.repo.load()), [self.tx])

    def test_delete_nonexistent(self):
        self.repo.save(self.tx)
        original = self.repo.path.read_bytes()
        result = self.repo.delete("TX-999")

        self.assertFalse(result)
        self.assertEqual(self.repo.path.read_bytes(), original)

    def test_update_nonexistent(self):
        self.repo.save(self.tx)
        original = self.repo.path.read_bytes()
        self.assertFalse(self.repo.update("TX-999", {"amount": 20000}))
        self.assertEqual(self.repo.path.read_bytes(), original)

    def test_next_id_uses_maximum_not_file_order(self):
        self.assertEqual(self.repo.next_id(), "TX-001")
        self.repo.save(replace(self.tx, id="TX-010"))
        self.repo.save(self.tx)
        self.assertEqual(self.repo.next_id(), "TX-011")

    def test_save_many_atomic_rollback(self):
        self.repo.save(self.tx)
        original = self.repo.path.read_bytes()

        def faulty_transactions():
            yield replace(self.tx, id="TX-002", amount=20000)
            raise RuntimeError("의도적인 저장 오류")

        with self.assertRaises(RuntimeError):
            self.repo.save_many_atomic(faulty_transactions())

        self.assertEqual(self.repo.path.read_bytes(), original)
        self.assertEqual(list(self.repo.path.parent.glob(".*.tmp")), [])
