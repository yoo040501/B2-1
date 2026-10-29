from .commands.transactions import (
    handle_add,
    handle_list,
    handle_update,
    handle_delete
)
from .commands.reports import handle_search, handle_summary
from .commands.management import handle_budget, handle_category
from .decorators import handle_errors
from .commands.csv_commands import handle_import, handle_export
# from .service import restore_categories
from .repository import TransactionRepository, CategoryStore, BudgetStore
from .parser import create_parser

@handle_errors
def main() -> int:
    parser = create_parser()
    args = parser.parse_args()
    BudgetStore(args.data_dir)

    # repo = TransactionRepository(args.data_dir)
    # category_store = CategoryStore(args.data_dir)
    # restored = restore_categories(repo, category_store)
    # if restored:
    #     print(f"[자동 복구] 누락된 카테고리: {', '.join(restored)}")
    handlers = {
            "add": handle_add,
            "list": handle_list,
            "search": handle_search,
            "summary": handle_summary,
            "budget": handle_budget,
            "category": handle_category,
            "update": handle_update,
            "delete": handle_delete,
            "import": handle_import,
            "export": handle_export,
        }
    return handlers[args.command](args)
