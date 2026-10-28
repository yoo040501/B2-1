from argparse import Namespace
from heapq import nlargest

from ..repository import TransactionRepository, BudgetStore
from ..service import search_transactions, summarize_month
from ..validators import validate_date_range, validate_month, validate_type
from ..decorators import time_action

@time_action
def handle_search(args: Namespace) -> int:
    validate_date_range(args.date_from, args.date_to)

    if args.limit <= 0:
        raise ValueError("--limit은 1 이상이어야 합니다.")

    if args.tx_type is not None:
        validate_type(args.tx_type)

    repo = TransactionRepository(args.data_dir)

    results = nlargest(
        args.limit,
        enumerate(search_transactions(
            repo,
            date_from=args.date_from,
            date_to=args.date_to,
            category=args.category,
            tx_type=args.tx_type,
            q=args.q,
            tag=args.tag
        )),
        key=lambda item: (item[1].date, item[0])
    )

    if not results:
        print("검색 결과가 없습니다.")

    for _, tx in results:
        print(tx)

    return 0

@time_action
def handle_summary(args: Namespace) -> int:
    validate_month(args.month)

    if args.top <= 0:
        raise ValueError("--top은 1 이상이어야 합니다.")

    repo = TransactionRepository(args.data_dir)

    income, expense, categories, count = summarize_month(
        repo, args.month
    )

    if count == 0:
        print("데이터 없음")

    print(f"\n{args.month} 월별 요약")
    print(f"총 수입: {income}원")
    print(f"총 지출: {expense}원")
    print(f"잔액: {income - expense}원")

    budget_store = BudgetStore(args.data_dir)
    budget = budget_store.get(args.month)

    if budget is not None:
        usage = (expense / budget) * 100

        print(f"예산: {budget}원 (사용률 {usage:.1f}%)")

        if expense > budget:
            print("[경고] 월 예산을 초과했습니다!")

    top_categories = sorted(
        categories.items(),
        key=lambda item: item[1],
        reverse=True
    )[:args.top]

    if not top_categories:
        print("\n지출 내역 없음")
    else:
        print(f"\n지출 TOP {args.top}")

        for i, (category, amount) in enumerate(
            top_categories, start=1
        ):
            print(f"{i}. {category}: {amount}원")

    return 0