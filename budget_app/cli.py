import argparse
from heapq import nlargest
from uuid import uuid4

from .models import Transaction
from .repository import TransactionRepository


def main() -> int:
    parser = argparse.ArgumentParser(description="콘솔 가계부")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("add", help="거래 추가")

    list_parser = subparsers.add_parser("list", help="거래 목록")
    list_parser.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()

    if args.command == "add":
        date = input("날짜(YYYY-MM-DD): ")
        tx_type = input("타입(income/expense): ")
        category = input("카테고리: ")
        amount = int(input("금액: "))
        memo = input("메모(선택): ")
        tags = [
            tag.strip()
            for tag in input("태그(쉼표 구분): ").split(",")
            if tag.strip()
        ]

        tx = Transaction(
            id=f"TX-{uuid4().hex}",
            date=date,
            type=tx_type,
            category=category,
            amount=amount,
            memo=memo,
            tags=tags
        )

        repo = TransactionRepository()
        repo.save(tx)

        print(f"[저장 완료] id={tx.id}")
    elif args.command == "list":
        repo = TransactionRepository()

        if args.limit <= 0:
            print("[오류] --limit은 1 이상이어야 합니다.")
            return 1

        transactions = nlargest(
            args.limit,
            enumerate(repo.load()),
            key=lambda item: (item[1].date, item[0])
        )

        for _, tx in transactions:
            print(tx)

    return 0