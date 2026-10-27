import argparse
from heapq import nlargest
from uuid import uuid4

from .models import Transaction
from .service import search_transactions, summarize_month
from .repository import TransactionRepository, BudgetStore, CategoryStore
from .csv_io import export_transactions, import_transactions
from .validators import validate_date, validate_type, validate_amount

def main() -> int:
    parser = argparse.ArgumentParser(description="콘솔 가계부")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("add", help="거래 추가")

    list_parser = subparsers.add_parser("list", help="거래 목록")
    list_parser.add_argument("--limit", type=int, default=10)

    search_parser = subparsers.add_parser("search", help="거래 검색")

    search_parser.add_argument("--from", dest="date_from")
    search_parser.add_argument("--to", dest="date_to")
    search_parser.add_argument("--category")
    search_parser.add_argument("--type", dest="tx_type")
    search_parser.add_argument("--q")
    search_parser.add_argument("--tag")
    search_parser.add_argument("--limit", type=int, default=20)
    summary_parser = subparsers.add_parser(
    "summary", help="월별 요약"
    )

    summary_parser.add_argument("--month", required=True)
    summary_parser.add_argument("--top", type=int, default=3)

    budget_parser = subparsers.add_parser(
    "budget", help="예산 관리"
    )

    budget_subparsers = budget_parser.add_subparsers(
        dest="budget_command", required=True
    )

    budget_set_parser = budget_subparsers.add_parser(
        "set", help="예산 설정"
    )

    budget_set_parser.add_argument("--month", required=True)
    budget_set_parser.add_argument("--amount", type=int, required=True)

    category_parser = subparsers.add_parser(
        "category", help="카테고리 관리"
    )

    category_subparsers = category_parser.add_subparsers(
        dest="category_command", required=True
    )

    category_subparsers.add_parser("add", help="카테고리 추가")
    category_subparsers.add_parser("list", help="카테고리 목록")
    category_subparsers.add_parser("remove", help="카테고리 삭제")

    delete_parser = subparsers.add_parser(
        "delete", help="거래 삭제"
    )
    delete_parser.add_argument("--id", required=True)

    update_parser = subparsers.add_parser(
    "update", help="거래 수정"
    )

    update_parser.add_argument("--id", required=True)
    update_parser.add_argument("--date")
    update_parser.add_argument("--type", dest="tx_type")
    update_parser.add_argument("--category")
    update_parser.add_argument("--amount", type=int)
    update_parser.add_argument("--memo")
    update_parser.add_argument("--tags")

    export_parser = subparsers.add_parser(
        "export", help="CSV 내보내기"
    )

    export_parser.add_argument("--out", required=True)
    export_parser.add_argument("--month")
    export_parser.add_argument("--from", dest="date_from")
    export_parser.add_argument("--to", dest="date_to")

    import_parser = subparsers.add_parser(
    "import", help="CSV 가져오기"
    )

    import_parser.add_argument(
        "--from", dest="input_file", required=True
    )


    args = parser.parse_args()

    if args.command == "add":
        date = input("날짜(YYYY-MM-DD): ")
        tx_type = input("타입(income/expense): ")
        category = input("카테고리: ").strip()

        category_store = CategoryStore()

        if category not in set(category_store.load()):
            print("[오류] 등록되지 않은 카테고리입니다.")
            print("[힌트] category add 명령어로 먼저 등록하세요.")
            return 1

        try:
            validate_date(date)
            validate_type(tx_type)

            amount = int(input("금액: "))
            validate_amount(amount)

        except ValueError as e:
            print(f"[오류] {e}")
            print("[힌트] 날짜, 타입, 금액을 확인하세요.")
            return 1
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
            key=lambda item: (item[1].date, item[0]) #lambda: 익명의 간단함수
        )

        for _, tx in transactions:
            print(tx)
    elif args.command == "search":
        if args.limit <= 0:
            print("[오류] --limit은 1 이상이어야 합니다.")
            return 1

        repo = TransactionRepository()

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
    elif args.command == "summary":
        if args.top <= 0:
            print("[오류] --top은 1 이상이어야 합니다.")
            return 1

        repo = TransactionRepository()

        income, expense, categories, count = summarize_month(
            repo, args.month
        )

        if count == 0:
            print("데이터 없음")

        print(f"\n{args.month} 월별 요약")
        print(f"총 수입: {income}원")
        print(f"총 지출: {expense}원")
        print(f"잔액: {income - expense}원")

        budget_store = BudgetStore()
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
    elif args.command == "budget":
        if args.budget_command == "set":
            if args.amount <= 0:
                print("[오류] 예산은 0보다 커야 합니다.")
                return 1

            store = BudgetStore()
            store.set(args.month, args.amount)

            print(f"[저장 완료] {args.month} 예산 {args.amount}원")
    elif args.command == "category":
        store = CategoryStore()

        if args.category_command == "add":
            name = input("카테고리명: ").strip()

            if store.add(name):
                print(f"[저장 완료] category={name}")
            else:
                print("[오류] 비어 있거나 이미 존재하는 카테고리입니다.")
                return 1

        elif args.category_command == "list":
            for name in store.load():
                print(f"- {name}")

        elif args.category_command == "remove":
            name = input("삭제할 카테고리명: ").strip()

            repo = TransactionRepository()

            if any(tx.category == name for tx in repo.load()):
                print("[오류] 사용 중인 카테고리는 삭제할 수 없습니다.")
                return 1

            if store.remove(name):
                print(f"[삭제 완료] category={name}")
            else:
                print("[오류] 존재하지 않는 카테고리입니다.")
                return 1
    elif args.command == "delete":
        repo = TransactionRepository()

        if repo.delete(args.id):
            print(f"[삭제 완료] id={args.id}")
        else:
            print(f"[오류] 존재하지 않는 거래입니다. id={args.id}")
            return 1

    elif args.command == "update":
        repo = TransactionRepository()

        changes = {}

        if args.date is not None:
            try:
                validate_date(args.date)
            except ValueError as e:
                print(f"[오류] {e}")
                return 1

            changes["date"] = args.date

        if args.tx_type is not None:
            try:
                validate_type(args.tx_type)
            except ValueError as e:
                print(f"[오류] {e}")
                return 1

            changes["type"] = args.tx_type

        if args.category is not None:
            if args.category not in set(CategoryStore().load()):
                print("[오류] 등록되지 않은 카테고리입니다.")
                return 1
            changes["category"] = args.category

        if args.amount is not None:
            if args.amount <= 0:
                print("[오류] 금액은 0보다 커야 합니다.")
                return 1
            changes["amount"] = args.amount

        if args.memo is not None:
            changes["memo"] = args.memo

        if args.tags is not None:
            changes["tags"] = [
                tag.strip()
                for tag in args.tags.split(",")
                if tag.strip()
            ]

        if not changes:
            print("[오류] 수정할 항목이 없습니다.")
            return 1

        if repo.update(args.id, changes):
            print(f"[수정 완료] id={args.id}")
        else:
            print(f"[오류] 존재하지 않는 거래입니다. id={args.id}")
            return 1

    elif args.command == "export":
        if not args.month and not (args.date_from and args.date_to):
            print("[오류] --month 또는 --from과 --to를 지정하세요.")
            return 1

        if bool(args.date_from) != bool(args.date_to):
            print("[오류] --from과 --to는 함께 지정해야 합니다.")
            return 1

        if args.date_from and args.date_from > args.date_to:
            print("[오류] 시작 날짜가 종료 날짜보다 늦습니다.")
            return 1

        repo = TransactionRepository()

        count = export_transactions(
            repo,
            out_file=args.out,
            month=args.month,
            date_from=args.date_from,
            date_to=args.date_to
        )

        print(f"[완료] {args.out} ({count} records)")
    elif args.command == "import":
        repo = TransactionRepository()
        category_store = CategoryStore()

        categories = set(category_store.load())

        try:
            imported, skipped = import_transactions(
                repo,
                csv_file=args.input_file,
                categories=categories
            )

        except (OSError, ValueError) as e:
            print(f"[오류] CSV 가져오기 실패: {e}")
            print("[힌트] 파일 경로와 CSV 헤더를 확인하세요.")
            return 1

        print(f"[완료] imported={imported}, skipped={skipped}")
    return 0
