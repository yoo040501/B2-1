from collections.abc import Iterator

from .models import Transaction
from .repository import TransactionRepository, CategoryStore


def search_transactions(
    repo: TransactionRepository,
    date_from: str | None = None,
    date_to: str | None = None,
    category: str | None = None,
    tx_type: str | None = None,
    q: str | None = None,
    tag: str | None = None
) -> Iterator[Transaction]:

    for tx in repo.load():
        if date_from and tx.date < date_from:
            continue

        if date_to and tx.date > date_to:
            continue

        if category and tx.category != category:
            continue

        if tx_type and tx.type != tx_type:
            continue

        if q and q.lower() not in tx.memo.lower():
            continue

        if tag and tag not in tx.tags:
            continue

        yield tx

from collections import defaultdict

def summarize_month(
    repo: TransactionRepository,
    month: str
) -> tuple[int, int, dict[str, int], int]:

    income = 0
    expense = 0
    category_totals = defaultdict(int) # 없는키에 접근하면 KeyError가 아니라 0으로 만들어줌
    count = 0

    for tx in repo.load():
        if not tx.date.startswith(month + "-"):
            continue

        count += 1

        if tx.type == "income":
            income += tx.amount

        elif tx.type == "expense":
            expense += tx.amount
            category_totals[tx.category] += tx.amount

    return income, expense, dict(category_totals), count

def restore_categories(
    repo: TransactionRepository,
    store: CategoryStore
) -> list[str]:

    registered = set(store.load()) #등록된 카테고리를 집합으로 만듦
    restored = []

    for tx in repo.load():
        if tx.category and tx.category not in registered: #거래가 사용하는 카테고리가 등록되어 있는지 검사
            if store.add(tx.category):
                registered.add(tx.category)
                restored.append(tx.category)

    return restored