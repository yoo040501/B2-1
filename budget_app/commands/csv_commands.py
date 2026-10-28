from argparse import Namespace
import csv
import sys

from ..repository import TransactionRepository, CategoryStore
from ..csv_io import import_transactions, export_transactions
from ..validators import validate_month, validate_date_range


def handle_export(args: Namespace) -> int:
    if args.month is not None:
        validate_month(args.month)

    validate_date_range(args.date_from, args.date_to)

    if not args.month and not (args.date_from and args.date_to):
        raise ValueError("--month 또는 --from과 --to를 지정하세요.")

    if bool(args.date_from) != bool(args.date_to):
        raise ValueError("--from과 --to는 함께 지정해야 합니다.")

    repo = TransactionRepository(args.data_dir)

    count = export_transactions(
        repo,
        out_file=args.out,
        month=args.month,
        date_from=args.date_from,
        date_to=args.date_to
    )

    print(f"[완료] {args.out} ({count} records)")
    return 0


def handle_import(args: Namespace) -> int:
    repo = TransactionRepository(args.data_dir)
    category_store = CategoryStore(args.data_dir)

    categories = set(category_store.load())

    try:
        imported, skipped = import_transactions(
            repo,
            csv_file=args.input_file,
            categories=categories
        )

    except csv.Error as e:
        print(f"[오류] CSV 형식이 잘못되었습니다: {e}",  file=sys.stderr)
        print("[힌트] CSV의 따옴표와 구분자를 확인하세요. 가져오기는 취소되었습니다.",  file=sys.stderr)
        return 1

    except (OSError, ValueError) as e:
        print(f"[오류] CSV 가져오기 실패: {e}", file=sys.stderr)
        print("[힌트] 파일 경로와 CSV 헤더를 확인하세요.", file=sys.stderr)
        return 1

    print(f"[완료] imported={imported}, skipped={skipped}")
    return 0
