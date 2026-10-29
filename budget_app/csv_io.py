import csv
from pathlib import Path

from .validators import validate_date, validate_type, validate_amount
from .repository import TransactionRepository, atomic_write
from .models import Transaction

def export_transactions(
    repo: TransactionRepository,
    out_file: str,
    month: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None
) -> int:

    path = Path(out_file).resolve()

	# 현재 사용하는 데이터 저장 파일 3개
    protected_paths = {
        (repo.path.parent / name).resolve()
        for name in (
            "transactions.jsonl",
            "categories.jsonl",
            "budgets.jsonl",
        )
    }

    if path in protected_paths:
        raise ValueError(
            "데이터 저장 파일에는 내보낼 수 없습니다. "
            "export.csv처럼 다른 파일을 지정하세요."
        )

    count = 0

  # 임시 파일에 작성하고, 모두 성공하면 최종 파일로 교체
    with atomic_write(path) as f:
        writer = csv.DictWriter(  # 딕셔너리를 csv파일에 기록하는 기능
            f,
            fieldnames=[
                "date", "type", "category",
                "amount", "memo", "tags"
            ]
        )
        writer.writeheader() #첫번째 줄에 칼럼 이름 기록

        for tx in repo.load():
            if month and not tx.date.startswith(month + "-"):
                continue

            if date_from and tx.date < date_from:
                continue

            if date_to and tx.date > date_to:
                continue

            writer.writerow({ #딕셔너리의 값을 CSV 한 줄로 저장
                "date": tx.date,
                "type": tx.type,
                "category": tx.category,
                "amount": tx.amount,
                "memo": tx.memo,
                "tags": ",".join(tx.tags)
            })

            count += 1

    return count

def import_transactions(
    repo: TransactionRepository,
    csv_file: str,
    categories: set[str]
) -> tuple[int, int]:

    skipped = 0

    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, strict=True) #CSV 파일을 한 줄씩 읽어서 딕셔너리로 변환

        fields = reader.fieldnames or []

        if len(fields) != len(set(fields)):
            raise ValueError("CSV 헤더에 중복된 이름이 있습니다.")
        
        required = {"date", "type", "category", "amount"}

        if not required.issubset(reader.fieldnames or []): #CSV 헤더에 필수 컬럼이 모두 있는지 확인하는 코드
            raise ValueError("CSV 필수 컬럼이 누락되었습니다.")

        # 최대 ID를 한 번만 조회
        next_number = int(repo.next_id().removeprefix("TX-"))
        def valid_transactions():
            nonlocal skipped, next_number

            for row in reader:
                try:
                    tx_date = (row["date"] or "").strip()
                    tx_type = (row["type"] or "").strip()
                    category = (row["category"] or "").strip()
                    amount = int(row["amount"])

                    validate_date(tx_date)
                    validate_type(tx_type)
                    validate_amount(amount)
                    
                    if category not in categories:
                        raise ValueError("등록되지 않은 카테고리")
                    if None in row:
                        raise ValueError("열 개수가 헤더보다 많습니다.")
                    memo = row.get("memo") or ""
                    tag_text = row.get("tags") or ""

                    tags = [
                        tag.strip()
                        for tag in tag_text.split(",")
                        if tag.strip()
                    ]

                    tx = Transaction(
                        id=f"TX-{next_number:03d}",
                        date=tx_date,
                        type=tx_type,
                        category=category,
                        amount=amount,
                        memo=memo,
                        tags=tags
                    )

                except (ValueError, TypeError, AttributeError):
                    skipped += 1
                    continue

                next_number += 1
                yield tx

        imported = repo.save_many_atomic(valid_transactions())

    return imported, skipped