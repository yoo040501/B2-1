from datetime import date
import re

def validate_date_range(
    date_from: str | None,
    date_to: str | None
) -> None:

    if date_from is not None:
        validate_date(date_from)

    if date_to is not None:
        validate_date(date_to)

    if date_from is not None and date_to is not None:
        if date_from > date_to:
            raise ValueError(
                "시작 날짜가 종료 날짜보다 늦을 수 없습니다."
            )

def validate_month(value: str) -> None:
    # 1. YYYY-MM 형식 확인
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}", value):
        raise ValueError("월은 YYYY-MM 형식이어야 합니다.")

    # 2. 실제 존재하는 월인지 확인
    year, month = map(int, value.split("-"))

    if not (1 <= year <= 9999):
        raise ValueError("존재하지 않는 연도입니다.")

    if not (1 <= month <= 12):
        raise ValueError("존재하지 않는 월입니다.")

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