from datetime import date


def validate_date(value: str) -> None:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise ValueError("올바르지 않은 날짜입니다.")

    if parsed.isoformat() != value:
        raise ValueError("날짜는 YYYY-MM-DD 형식이어야 합니다.")


def validate_type(value: str) -> None:
    if value not in ("income", "expense"):
        raise ValueError("타입은 income 또는 expense여야 합니다.")


def validate_amount(value: int) -> None:
    if value <= 0:
        raise ValueError("금액은 0보다 커야 합니다.")