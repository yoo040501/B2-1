import json
import os
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from pathlib import Path
from dataclasses import asdict
from collections.abc import Generator
from typing import Any, TextIO

from .models import Transaction
from .decorators import log_action


def read_jsonl(path: Path) -> Generator[dict[str, Any]]:
    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as src:
        for line in src:
            if not line.strip():
                continue
            data = json.loads(line)  #JSON 문자열을 Python 딕셔너리로 변환
            if not isinstance(data, dict):
                raise ValueError(f"JSONL 형식 오류: {path}에 객체가 아닌 값이 있습니다.")
            yield data


def write_jsonl(dest: TextIO, data: dict[str, Any]) -> None:
    dest.write(json.dumps(data, ensure_ascii=False) + "\n")


@contextmanager #with 문에서 사용할 수 있는 함수 형태의 컨텍스트 매니저를 만드는 데코레이터
def atomic_write(path: Path) -> Generator[TextIO]:
    temp_path: Path | None = None

    try:
        with NamedTemporaryFile(
            mode="w", #쓰기 모드
            encoding="utf-8", 
            dir=path.parent, #원본과 같은 폴더에 생성
            prefix=f".{path.name}.",
            suffix=".tmp", #임시 파일확장자 .tmp
            delete=False #파일을 닫아도 자동 삭제 X
        ) as dest:
            temp_path = Path(dest.name)
            yield dest
            dest.flush()
            os.fsync(dest.fileno())

        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

class TransactionRepository:
    def __init__(self, data_dir: str = "data"):
        self.path = Path(data_dir) / "transactions.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @log_action
    def save(self, tx: Transaction) -> None:
        if any(existing.id == tx.id for existing in self.load()):
            raise ValueError(f"이미 존재하는 거래 ID입니다: {tx.id}")
            
        with self.path.open("a", encoding="utf-8") as dest:
            write_jsonl(dest, asdict(tx))#asdict(): 객체를 딕셔너리로 변환

    def load(self) -> Generator[Transaction]:
        for data in read_jsonl(self.path):
            yield Transaction(**data)  #**는 딕셔너리의 키와 값을 함수의 키워드 인자로 풀어줌

    @log_action
    def delete(self, tx_id: str) -> bool:
        if not any(tx.id == tx_id for tx in self.load()):
            return False

        with atomic_write(self.path) as dest:
            for data in read_jsonl(self.path):
                if data["id"] != tx_id:
                    write_jsonl(dest, data)
        return True

    @log_action
    def update(self, tx_id: str, changes: dict) -> bool:
        if not any(tx.id == tx_id for tx in self.load()):
            return False

        with atomic_write(self.path) as dest:
            for data in read_jsonl(self.path):
                if data["id"] == tx_id:
                    data.update(changes)
                write_jsonl(dest, data)
        return True

    def next_id(self) -> str:
        last_id = 0

        for tx in self.load():
            number = tx.id.removeprefix("TX-")

            if number.isdigit():
                last_id = max(last_id, int(number))

        return f"TX-{last_id + 1:03d}"
    
class BudgetStore:
    def __init__(self, data_dir: str = "data"):
        self.path = Path(data_dir) / "budgets.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def set(self, month: str, amount: int) -> None:     #해당 월 예산 저장 또는 변경
        with atomic_write(self.path) as dest:
            for data in read_jsonl(self.path):
                if data["month"] != month:
                    write_jsonl(dest, data)
            write_jsonl(dest, {"month": month, "amount": amount})

    def get(self, month: str) -> int | None:        #해당 월의 예산 조회
        for data in read_jsonl(self.path):
            if data["month"] == month:
                return data["amount"]
        return None

class CategoryStore:
    def __init__(self, data_dir: str = "data"):
        self.path = Path(data_dir) / "categories.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

        if not self.path.exists():
            defaults = ["food", "transport", "rent", "salary", "etc"]
            with self.path.open("w", encoding="utf-8") as dest:
                for name in defaults:
                    write_jsonl(dest, {"name": name})

    def load(self) -> Generator[str]:
        for data in read_jsonl(self.path):
            yield data["name"]

    def add(self, name: str) -> bool:
        name = name.strip()
        if not name or name in self.load():
            return False

        with self.path.open("a", encoding="utf-8") as dest:
            write_jsonl(dest, {"name": name})
        return True

    def remove(self, name: str) -> bool:
        if name not in self.load():
            return False

        with atomic_write(self.path) as dest:
            for data in read_jsonl(self.path):
                if data["name"] != name:
                    write_jsonl(dest, data)
        return True