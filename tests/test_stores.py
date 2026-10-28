import unittest
from tempfile import TemporaryDirectory

from budget_app.repository import CategoryStore, BudgetStore


class TestCategoryStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.store = CategoryStore(self.temp_dir.name)

    def test_add_category(self):
        result = self.store.add("books")

        self.assertTrue(result)
        self.assertIn("books", CategoryStore(self.temp_dir.name).load())

    def test_duplicate_category(self):
        self.store.add("books")

        result = self.store.add("books")

        self.assertFalse(result)
        self.assertEqual(list(self.store.load()).count("books"), 1)

    def test_remove_category(self):
        self.store.add("books")
        original = set(self.store.load())

        result = self.store.remove("books")

        self.assertTrue(result)
        self.assertEqual(set(self.store.load()), original - {"books"})

    def test_remove_nonexistent_preserves_categories(self):
        original = self.store.path.read_bytes()
        self.assertFalse(self.store.remove("not-registered"))
        self.assertEqual(self.store.path.read_bytes(), original)

    def test_blank_category_is_rejected(self):
        original = self.store.path.read_bytes()
        self.assertFalse(self.store.add("   "))
        self.assertEqual(self.store.path.read_bytes(), original)


class TestBudgetStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.store = BudgetStore(self.temp_dir.name)

    def test_set_and_get(self):
        self.store.set("2026-10", 100000)

        result = BudgetStore(self.temp_dir.name).get("2026-10")

        self.assertEqual(result, 100000)

    def test_update_budget(self):
        self.store.set("2026-10", 100000)
        self.store.set("2026-11", 300000)
        self.store.set("2026-10", 200000)

        result = self.store.get("2026-10")

        self.assertEqual(result, 200000)
        self.assertEqual(self.store.get("2026-11"), 300000)

    def test_missing_budget(self):
        self.assertIsNone(self.store.get("2026-10"))
