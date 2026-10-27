import unittest
from tempfile import TemporaryDirectory

from budget_app.models import Transaction
from budget_app.repository import TransactionRepository


class TestTransactionRepository(unittest.TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.repo = TransactionRepository(self.temp_dir.name)

        self.tx = Transaction(
            id="TX-001",
            date="2026-10-27",
            type="expense",
            category="food",
            amount=15000
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load(self):
        self.repo.save(self.tx)

        transactions = list(self.repo.load())

        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0].amount, 15000)

    def test_update(self):
        self.repo.save(self.tx)

        result = self.repo.update(
            "TX-001",
            {"amount": 20000}
        )

        self.assertTrue(result)
        self.assertEqual(
            list(self.repo.load())[0].amount,
            20000
        )

    def test_delete(self):
        self.repo.save(self.tx)

        result = self.repo.delete("TX-001")

        self.assertTrue(result)
        self.assertEqual(len(list(self.repo.load())), 0)

    def test_duplicate_id(self):
        self.repo.save(self.tx)

        with self.assertRaises(ValueError):
            self.repo.save(self.tx)

    def test_delete_nonexistent(self):
        result = self.repo.delete("TX-999")

        self.assertFalse(result)

def test_save_many_atomic_rollback(self):
    # 기존 거래 저장
    self.repo.save(self.tx)

    # 첫 번째 거래를 전달한 다음 오류 발생
    def faulty_transactions():
        yield Transaction(
            id="TX-002",
            date="2026-10-27",
            type="expense",
            category="food",
            amount=20000
        )

        raise RuntimeError("의도적인 저장 오류")

    # 오류 발생 확인
    with self.assertRaises(RuntimeError):
        self.repo.save_many_atomic(faulty_transactions())

    # 기존 거래는 그대로, 새 거래는 저장되지 않아야 함
    transactions = list(self.repo.load())

    self.assertEqual(len(transactions), 1)
    self.assertEqual(transactions[0].id, "TX-001")
    self.assertEqual(transactions[0].amount, 15000)