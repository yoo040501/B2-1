import json
import os
from itertools import chain
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from pathlib import Path
from dataclasses import asdict
from collections.abc import Generator
from typing import Any, TextIO

from .models import Transaction
from .decorators import log_action


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    record = (json.dumps(data, ensure_ascii=False) + "\n").encode("utf-8") #문자열을 바이트로 변환

    with path.open("a+b") as dest: #추가 저장하면서 읽기도 가능한 바이너리 모드로 열기
        dest.seek(0, os.SEEK_END)
        prefix = b""

        if dest.tell() > 0:  # 빈 파일이 아니면
            dest.seek(-1, os.SEEK_END)

            if dest.read(1) != b"\n":
                prefix = b"\n"

        dest.write(prefix + record)

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



#Atomic write란? 데이터가 영구 저장소에 완전히 기록되거나 전혀 기록되지 않도록 보장하는 쓰기 작업의 원자성을 의미
@contextmanager #with 문에서 사용할 수 있는 함수 형태의 컨텍스트 매니저를 만드는 데코레이터
def atomic_write(path: Path) -> Generator[TextIO]:
    temp_path: Path | None = None

    try:
        with NamedTemporaryFile(
            mode="w", #쓰기 모드
            encoding="utf-8", 
            dir=path.parent, #원본과 같은 폴더에 생성
			newline="",          # 추가: CSV 줄바꿈 처리
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
        if not self.path.exists():
            self.path.touch()

    @log_action
    def save(self, tx: Transaction) -> None:
        if any(existing.id == tx.id for existing in self.load()):
            raise ValueError(f"이미 존재하는 거래 ID입니다: {tx.id}")
            
        append_jsonl(self.path, asdict(tx))#asdict(): 객체를 딕셔너리로 변환

    def load(self) -> Generator[Transaction]:
        for data in read_jsonl(self.path):
            try:
                tx = Transaction(**data)  #**는 딕셔너리의 키와 값을 함수의 키워드 인자로 풀어줌
            except TypeError as e:
                raise ValueError(
                    f"{self.path}: 거래 항목이 누락되었거나 잘못됐습니다. "
                    "저장 파일을 확인하세요."
                ) from e

            yield tx

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

    def save_many_atomic(self, transactions: Generator[Transaction]) -> int:
        iterator = iter(transactions)
        first = next(iterator, None)

        # 정상 거래가 없으면 파일을 재작성하지 않음
        if first is None:
            return 0

        count = 0

        with atomic_write(self.path) as dest:
            # 기존 거래 복사
            for tx in self.load():
                write_jsonl(dest, asdict(tx))

            # 미리 꺼낸 첫 거래와 나머지 거래 저장
            for tx in chain((first,), iterator):
                write_jsonl(dest, asdict(tx))
                count += 1

        return count
    
class BudgetStore:
    def __init__(self, data_dir: str = "data"):
        self.path = Path(data_dir) / "budgets.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def set(self, month: str, amount: int) -> None:     #해당 월 예산 저장 또는 변경
        with atomic_write(self.path) as dest:
            for data in read_jsonl(self.path):
                if data["month"] != month:
                    write_jsonl(dest, data)
            write_jsonl(dest, {"month": month, "amount": amount})

    def get(self, month: str) -> int | None:
        for data in read_jsonl(self.path):
            if "month" not in data or "amount" not in data:
                raise ValueError(
                    f"{self.path}: 예산의 month 또는 amount가 없습니다."
                )

            if data["month"] == month:
                amount = data["amount"]

                if type(amount) is not int or amount <= 0:
                    raise ValueError(
                        f"{self.path}: 예산 금액은 양수 정수여야 합니다. "
                        "저장 파일을 확인하세요."
                    )

                return amount

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
            if "name" not in data:
                raise ValueError(
                    f"{self.path}: 카테고리 이름(name)이 없습니다. "
                    "저장 파일을 확인하세요."
                )

            yield data["name"]

    def add(self, name: str) -> bool:
        name = name.strip()
        if not name or name in self.load():
            return False

        append_jsonl(self.path, {"name": name})
        return True

    def remove(self, name: str) -> bool:
        if name not in self.load():
            return False

        with atomic_write(self.path) as dest:
            for data in read_jsonl(self.path):
                if data["name"] != name:
                    write_jsonl(dest, data)
        return True