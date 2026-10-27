import unittest
from tempfile import TemporaryDirectory

from budget_app.repository import CategoryStore, BudgetStore


class TestCategoryStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.store = CategoryStore(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_category(self):
        result = self.store.add("books")

        self.assertTrue(result)
        self.assertIn("books", self.store.load())

    def test_duplicate_category(self):
        self.store.add("books")

        result = self.store.add("books")

        self.assertFalse(result)

    def test_remove_category(self):
        self.store.add("books")

        result = self.store.remove("books")

        self.assertTrue(result)
        self.assertNotIn("books", self.store.load())


class TestBudgetStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.store = BudgetStore(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_set_and_get(self):
        self.store.set("2026-10", 100000)

        result = self.store.get("2026-10")

        self.assertEqual(result, 100000)

    def test_update_budget(self):
        self.store.set("2026-10", 100000)
        self.store.set("2026-10", 200000)

        result = self.store.get("2026-10")

        self.assertEqual(result, 200000)