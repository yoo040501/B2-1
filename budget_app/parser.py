import argparse

from .validators import parse_amount

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="CLI 가계부 프로그램"
    )

    parser.add_argument(
        "--data-dir",
        default="data",
        help="데이터 저장 디렉터리"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

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
    budget_set_parser.add_argument("--amount", type=amount_argument, required=True)

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
    update_parser.add_argument("--amount", type=amount_argument)
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

    return parser

def amount_argument(value: str) -> int:
    try:
        return parse_amount(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e)) from None