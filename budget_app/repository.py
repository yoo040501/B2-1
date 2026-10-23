import json
from pathlib import Path
from dataclasses import asdict
from collections.abc import Iterator
from .models import Transaction

class TransactionRepository:
    def __init__(self, data_dir: str = "data"):
        self.path = Path(data_dir) / "transactions.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, tx: Transaction) -> None:
        path = Path("data/transactions.jsonl")

        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(tx), ensure_ascii=False) + "\n") #asdict(): 객체를 딕셔너리로 변환

    def load(self) -> Iterator[Transaction]:
        if not self.path.exists():
            return
        
        with open("data/transactions.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line) #JSON 문자열을 Python 딕셔너리로 변환
                yield Transaction(**data) #**는 딕셔너리의 키와 값을 함수의 키워드 인자로 풀어줌


