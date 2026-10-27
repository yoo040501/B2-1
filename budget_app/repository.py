import json
import os

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

    def delete(self, tx_id: str) -> bool:
        if not self.path.exists():
            return False

        temp_path = self.path.with_suffix(".jsonl.tmp")
        found = False

        with open(self.path, "r", encoding="utf-8") as src:
            with open(temp_path, "w", encoding="utf-8") as dest:
                for line in src:
                    data = json.loads(line)

                    if data["id"] == tx_id: # id가 일치하면 임시파일에 저장 X
                        found = True
                        continue

                    dest.write(line)

        if not found:
            temp_path.unlink() #삭제할 id를 못찾았으면 임시파일 제거
            return False

        os.replace(temp_path, self.path)
        return True

    def update(self, tx_id: str, changes: dict) -> bool:
        if not self.path.exists():
            return False

        temp_path = self.path.with_suffix(".jsonl.tmp")
        found = False

        with open(self.path, "r", encoding="utf-8") as src:
            with open(temp_path, "w", encoding="utf-8") as dest:
                for line in src:
                    data = json.loads(line)

                    if data["id"] == tx_id:
                        data.update(changes)
                        found = True

                    dest.write(json.dumps(data, ensure_ascii=False) + "\n")

        if not found:
            temp_path.unlink()
            return False

        os.replace(temp_path, self.path)
        return True
    
class BudgetStore:
    def __init__(self, data_dir: str = "data"):
        self.path = Path(data_dir) / "budgets.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def set(self, month: str, amount: int) -> None:     #해당 월 예산 저장 또는 변경
        temp_path = self.path.with_suffix(".jsonl.tmp")

        with open(temp_path, "w", encoding="utf-8") as dest:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as src:
                    for line in src:
                        if not line.strip():
                            continue

                        data = json.loads(line)

                        if data["month"] != month:
                            dest.write(json.dumps(data) + "\n")

            budget = {"month": month, "amount": amount}
            dest.write(json.dumps(budget) + "\n")

        os.replace(temp_path, self.path)

    def get(self, month: str) -> int | None:        #해당 월의 예산 조회
        if not self.path.exists():
            return None

        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                data = json.loads(line)

                if data["month"] == month:
                    return data["amount"]

        return None

class CategoryStore:
    def __init__(self, data_dir: str = "data"):
        self.path = Path(data_dir) / "categories.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            defaults = ["food", "transport", "rent", "salary", "etc"]

            with open(self.path, "w", encoding="utf-8") as f:
                for name in defaults:
                    f.write(json.dumps({"name": name}) + "\n")

    def load(self) -> Iterator[str]:
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    yield data["name"]

    def add(self, name: str) -> bool:
        name = name.strip()

        if not name or name in self.load():
            return False

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"name": name}, ensure_ascii=False) + "\n")

        return True

    def remove(self, name: str) -> bool:
        if name not in self.load():
            return False

        temp_path = self.path.with_suffix(".jsonl.tmp")

        with open(temp_path, "w", encoding="utf-8") as f:
            for category in self.load():
                if category != name:
                    f.write(json.dumps({"name": category}, ensure_ascii=False) + "\n")

        os.replace(temp_path, self.path)
        return True