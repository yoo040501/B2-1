from argparse import Namespace

from ..repository import (
    TransactionRepository,
    BudgetStore,
    CategoryStore
)
from ..validators import validate_month


def handle_budget(args: Namespace) -> int:
    if args.budget_command == "set":
        validate_month(args.month)

        if args.amount <= 0:
            raise ValueError("예산은 0보다 커야 합니다.")

        store = BudgetStore(args.data_dir)
        store.set(args.month, args.amount)

        print(f"[저장 완료] {args.month} 예산 {args.amount}원")

    return 0


def handle_category(args: Namespace) -> int:
    store = CategoryStore(args.data_dir)

    if args.category_command == "add":
        name = input("카테고리명: ").strip()

        if store.add(name):
            print(f"[저장 완료] category={name}")
        else:
            raise ValueError("비어 있거나 이미 존재하는 카테고리입니다.")

    elif args.category_command == "list":
        for name in store.load():
            print(f"- {name}")

    elif args.category_command == "remove":
        name = input("삭제할 카테고리명: ").strip()

        repo = TransactionRepository(args.data_dir)

        if any(tx.category == name for tx in repo.load()):
            raise ValueError("사용 중인 카테고리는 삭제할 수 없습니다.")

        if store.remove(name):
            print(f"[삭제 완료] category={name}")
        else:
            raise ValueError("존재하지 않는 카테고리입니다.")

    return 0