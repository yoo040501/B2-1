import csv
from pathlib import Path

from .repository import TransactionRepository
from uuid import uuid4
from datetime import date

from .models import Transaction

def export_transactions(
    repo: TransactionRepository,
    out_file: str,
    month: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None
) -> int:

    path = Path(out_file)
    count = 0

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(            # 딕셔너리를 csv파일에 기록하는 기능
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

    imported = 0
    skipped = 0

    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f) #CSV 파일을 한 줄씩 읽어서 딕셔너리로 변환

        required = {"date", "type", "category", "amount"}

        if not required.issubset(reader.fieldnames or []): #CSV 헤더에 필수 컬럼이 모두 있는지 확인하는 코드
            raise ValueError("CSV 필수 컬럼이 누락되었습니다.")

        for row in reader:
            try:
                tx_date = (row["date"] or "").strip()
                tx_type = (row["type"] or "").strip()
                category = (row["category"] or "").strip()
                amount = int(row["amount"])

                # 입력값 검증
                parsed_date = date.fromisoformat(tx_date) 

                if parsed_date.isoformat() != tx_date:
                    raise ValueError("날짜 형식 오류")

                if tx_type not in ("income", "expense"):
                    raise ValueError("잘못된 거래 타입")

                if amount <= 0:
                    raise ValueError("금액은 양수여야 합니다.")

                if category not in categories:
                    raise ValueError("등록되지 않은 카테고리")

                memo = row.get("memo") or ""
                tag_text = row.get("tags") or ""

                tags = [
                    tag.strip()
                    for tag in tag_text.split(",")
                    if tag.strip()
                ]

                tx = Transaction(
                    id=f"TX-{uuid4().hex}",
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

            repo.save(tx)
            imported += 1

    return imported, skipped