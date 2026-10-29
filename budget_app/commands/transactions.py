from datetime import date
from argparse import Namespace

from ..models import Transaction
from ..repository import TransactionRepository, CategoryStore
from ..validators import validate_date, validate_type, validate_amount, validate_category, parse_tags, parse_amount
from ..service import latest_transactions

def handle_add(args: Namespace) -> int:
    tx_date = input("날짜(YYYY-MM-DD, 엔터 시 오늘): ").strip() or date.today().isoformat()
    validate_date(tx_date)
    tx_type = input("타입(income/expense): ").strip()
    validate_type(tx_type)

    category = input("카테고리: ").strip()

    category_store = CategoryStore(args.data_dir)

    validate_category(category, set(category_store.load()))

    amount = parse_amount(input("금액: "))

    memo = input("메모(선택): ")
    tags = parse_tags(input("태그(쉼표 구분): "))

    repo = TransactionRepository(args.data_dir)

    tx = Transaction(
        id=repo.next_id(),
        date=tx_date,
        type=tx_type,
        category=category,
        amount=amount,
        memo=memo,
        tags=tags
    )

    repo.save(tx)

    print(f"[저장 완료] id={tx.id}")
    return 0

def handle_list(args: Namespace) -> int:
    repo = TransactionRepository(args.data_dir)

    if args.limit <= 0:
        raise ValueError("--limit은 1 이상이어야 합니다.")

    transactions = latest_transactions(repo.load(), args.limit)

    if not transactions:
        print("등록된 거래가 없습니다.")
    else:
        for tx in transactions:
            print(tx)

    
    return 0

def handle_delete(args: Namespace) -> int:
    repo = TransactionRepository(args.data_dir)

    if repo.delete(args.id):
        print(f"[삭제 완료] id={args.id}")
    else:
        raise ValueError(f"존재하지 않는 거래입니다. id={args.id}")

    return 0

def handle_update(args: Namespace) -> int:
    repo = TransactionRepository(args.data_dir)
    changes = {}

    if args.date is not None:
        validate_date(args.date)
        changes["date"] = args.date

    if args.tx_type is not None:
        validate_type(args.tx_type)
        changes["type"] = args.tx_type

    if args.category is not None:
        validate_category(
            args.category,
            set(CategoryStore(args.data_dir).load()),
        )
        changes["category"] = args.category

    if args.amount is not None:
        validate_amount(args.amount)
        changes["amount"] = args.amount

    if args.memo is not None:
        changes["memo"] = args.memo

    if args.tags is not None:
        changes["tags"] = parse_tags(args.tags)
    if not changes:
        raise ValueError("수정할 항목이 없습니다.")

    if repo.update(args.id, changes):
        print(f"[수정 완료] id={args.id}")
    else:
        raise ValueError(f"존재하지 않는 거래입니다. id={args.id}")

    return 0