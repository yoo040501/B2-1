import unittest

from budget_app.validators import (
    validate_date,
    validate_type,
    validate_amount,
    validate_month,
    validate_date_range,
)


class TestValidators(unittest.TestCase):

    def test_valid_date(self):
        validate_date("2026-10-27")
        validate_date("2024-02-29")

    def test_invalid_date(self):
        for value in ("2026-13-01", "2026-02-30", "2026-02-29", "2026-1-01", "20261027", ""):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_date(value)

    def test_valid_type(self):
        validate_type("income")
        validate_type("expense")

    def test_invalid_type(self):
        with self.assertRaises(ValueError):
            validate_type("unknown")

    def test_valid_amount(self):
        validate_amount(1000)

    def test_invalid_amount(self):
        with self.assertRaises(ValueError):
            validate_amount(0)

        with self.assertRaises(ValueError):
            validate_amount(-100)

    def test_valid_month(self):
        validate_month("2026-10")

    def test_invalid_month(self):
        for value in ("2026-13", "2026-00", "2026-1", "0000-01", "2026-10-01", ""):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_month(value)

    def test_valid_date_ranges(self):
        for start, end in (
            (None, None), ("2026-10-01", None), (None, "2026-10-31"),
            ("2026-10-01", "2026-10-01"), ("2026-10-01", "2026-10-31"),
        ):
            with self.subTest(start=start, end=end):
                validate_date_range(start, end)

    def test_invalid_date_range(self):
        with self.assertRaises(ValueError):
            validate_date_range(
                "2026-10-31",
                "2026-10-01"
            )
