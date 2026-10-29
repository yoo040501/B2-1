# 제너레이터와 데코레이터 이해하기

이 문서는 [CLI 가계부 프로그램](README.md)의 제너레이터와 데코레이터를 예시로 설명합니다. 설명용 코드는 앱을 수정하라는 뜻이 아니라, 현재 구현의 동작을 이해하기 위한 예시입니다.

각 `python` 코드 블록은 독립적인 예시입니다. Python 파일로 저장해 실행할 수 있으며, 프로젝트 모듈을 import하는 예시 파일은 저장소 최상위 폴더에 두고 실행합니다.

## 1. 제너레이터: 값을 하나씩 전달하는 함수

### return과 yield의 차이

일반 함수는 `return`으로 결과를 반환하고 종료합니다.

```python
def make_numbers():
    return [10, 20]

print(make_numbers())
```

출력:

```text
[10, 20]
```

이 함수는 반환할 목록을 먼저 만듭니다. 반면 `yield`가 있는 함수는 호출하면 **제너레이터 객체**를 반환하고, 값을 요청받을 때 본문을 실행합니다.

```python
def numbers():
    print("첫 번째 값 준비")
    yield 10

    print("두 번째 값 준비")
    yield 20

gen = numbers()
print("제너레이터 생성 완료")

print(next(gen))
print(next(gen))
print(next(gen, "끝"))
```

출력:

```text
제너레이터 생성 완료
첫 번째 값 준비
10
두 번째 값 준비
20
끝
```

실행 순서는 다음과 같습니다.

1. `numbers()`는 제너레이터 객체를 만듭니다. 아직 본문은 실행하지 않습니다.
2. 첫 `next(gen)`에서 `yield 10`까지 실행하고 10을 전달한 뒤 멈춥니다.
3. 다음 `next(gen)`에서 멈춘 다음 부분부터 실행하고 20을 전달합니다.
4. 끝까지 실행한 뒤 더 요청하면 `StopIteration`이 발생합니다. 여기서는 `next(gen, "끝")`으로 기본값을 지정했으므로 예외 대신 `"끝"`을 받습니다.

`yield`는 현재 실행 위치와 지역 변수 상태를 유지합니다. `return`처럼 함수를 완전히 끝내는 것이 아닙니다.

### for문과 한 번만 소비되는 특성

`for`문이 내부적으로 다음 값을 요청하고 종료도 처리하므로, 보통 직접 `next()`를 반복해서 호출할 필요는 없습니다.

```python
def numbers():
    yield 10
    yield 20

gen = numbers()

for number in gen:
    print(number)

print(list(gen))
print(list(numbers()))
```

출력:

```text
10
20
[]
[10, 20]
```

`gen`은 이미 끝까지 소비했으므로 다시 읽을 값이 없습니다. 같은 데이터를 다시 처리하려면 `numbers()`를 다시 호출해 새 제너레이터를 만듭니다. 가계부에서도 조회할 때마다 `repo.load()`를 새로 호출합니다.

### 실제 코드: JSONL을 한 줄씩 읽기

[repository.py](../budget_app/repository.py)의 `read_jsonl()`은 파일 전체를 한 번에 읽지 않고, 한 줄씩 JSON 객체로 변환해 `yield`합니다.

다음 예시는 실제 함수를 사용합니다. 임시 폴더만 사용하므로 기본 `data/`는 바뀌지 않습니다.

```python
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from budget_app.repository import read_jsonl

with TemporaryDirectory() as directory:
    path = Path(directory) / "example.jsonl"
    path.write_text(
        json.dumps({"amount": 1000}) + "\n"
        + json.dumps({"amount": 2000}) + "\n",
        encoding="utf-8",
    )

    records = read_jsonl(path)
    print("읽기 시작 전")

    for record in records:
        print(record["amount"])
```

출력:

```text
읽기 시작 전
1000
2000
````

records = read_jsonl(path)`에서는 아직 파일을 읽지 않습니다. `for`문이 값을 요청할 때 파일을 열고, 줄을 읽고, JSON을 해석합니다. 따라서 파일 형식 오류도 제너레이터를 생성할 때가 아니라 **실제로 순회할 때** 발생할 수 있습니다.

거래를 읽는 전체 흐름은 다음과 같습니다.

```text
파일의 한 줄
    → read_jsonl(): JSON 딕셔너리로 변환
    → TransactionRepository.load(): Transaction 객체로 변환
    → search_transactions(): 조건에 맞는 거래만 전달
    → latest_transactions(): 최신순 상위 N개 선택
    → handler: 화면에 출력
```

`read_jsonl()`이 딕셔너리를 전달하면 `load()`가 거래 객체로 바꿔 다시 전달합니다. `search_transactions()`도 목록 전체를 만들지 않고, 조건에 맞는 거래만 `yield`합니다.

### 실제 코드: 최신 거래를 고르는 동안 메모리 사용 줄이기

다음은 [service.py](../budget_app/service.py)의 `latest_transactions()`를 사용하는 예시입니다.

```python
from budget_app.models import Transaction
from budget_app.service import latest_transactions

def example_transactions():
    yield Transaction(
        id="TX-001", date="2026-10-10",
        type="expense", category="food", amount=1000,
    )
    yield Transaction(
        id="TX-002", date="2026-10-29",
        type="expense", category="food", amount=2000,
    )
    yield Transaction(
        id="TX-003", date="2026-10-10",
        type="expense", category="food", amount=3000,
    )

selected = latest_transactions(example_transactions(), limit=2)
print([tx.id for tx in selected])
```

출력:

```text
['TX-002', 'TX-003']
```

날짜가 가장 최신인 `TX-002`가 먼저이고, 같은 날짜에서는 입력 순서가 뒤인 `TX-003`을 우선합니다.

최신 2건을 찾으려면 입력 거래를 모두 확인해야 합니다. 하지만 `heapq.nlargest()`는 상위 개수에 비례하는 거래만 보관하므로 전체 거래를 먼저 리스트로 만들 필요는 없습니다.

| 처리 방법 | 거래를 메모리에 보관하는 규모 |
|---|---|
| `list(repo.load())`로 전체를 모으기 | 전체 거래 수에 비례 |
| 현재 목록·검색처럼 상위 N개만 선택하기 | 출력 제한 N에 비례 |
| 월별 요약에서 합계만 누적하기 | 합계 변수와 카테고리 수에 비례 |

제너레이터를 사용한다고 항상 메모리를 적게 사용하는 것은 아닙니다. `list(generator)`로 감싸면 전체 결과를 모으게 됩니다. 또한 한 줄의 크기와 등록 카테고리 집합 등도 메모리를 사용하므로 모든 처리가 고정 크기 메모리만 사용하는 것은 아닙니다.

## 2. 데코레이터: 기존 함수에 공통 기능 붙이기

### 함수마다 반복하는 작업 분리하기

거래 저장·수정·삭제 전에 로그를 남기려면 각 함수에 비슷한 `print()`를 작성할 수 있습니다. 데코레이터는 이런 공통 작업을 한 곳으로 분리하고 필요한 함수에 적용하는 방법입니다.

[decorators.py](../budget_app/decorators.py)의 `log_action`을 반환 부분만 간단히 정리하면 다음 구조입니다.

```python
import sys
from functools import wraps

def log_action(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"[LOG] {func.__name__} 실행", file=sys.stderr)
        return func(*args, **kwargs)

    return wrapper

@log_action
def calculate_total(amount, count=1):
    return amount * count

print(calculate_total(1000, count=2))
print(calculate_total.__name__)
```

stdout:

```text
2000
calculate_total
```

stderr:

```text
[LOG] calculate_total 실행
```

각 부분의 역할은 다음과 같습니다.

| 코드 | 역할 |
|---|---|
| `func` | 공통 기능을 붙일 원래 함수 |
| `wrapper` | 로그를 출력하고 원래 함수를 실행하는 새 함수 |
| `*args` | 전달받은 위치 인자. 예시에서는 `1000` |
| `**kwargs` | 전달받은 키워드 인자. 예시에서는 `count=2` |
| `func(*args, **kwargs)` | 인자를 그대로 넘겨 원래 함수 실행 |
| `return func(...)` | 원래 함수의 반환값을 호출한 쪽에 전달 |
| `@wraps(func)` | 원래 함수의 이름·설명 같은 정보를 유지 |
| `return wrapper` | 감싼 함수를 반환 |

`@log_action`을 붙이는 것은 함수 정의 뒤에 다음처럼 다시 대입하는 것과 같습니다.

```text
calculate_total = log_action(calculate_total)
```

호출 흐름은 다음과 같습니다.

```text
calculate_total(1000, count=2)
    → wrapper(1000, count=2)
    → 로그 출력
    → 원래 calculate_total(1000, count=2) 실행
    → 결과 2000 반환
```

데코레이터를 적용하는 작업은 함수가 정의될 때 이루어집니다. 실제 로그 출력은 이후 감싼 함수를 호출할 때마다 실행됩니다.

가계부에서는 `TransactionRepository.save()`·`update()`·`delete()`에 `@log_action`을 붙였습니다. 각 함수는 거래 처리에 집중하고, 실행 시작 로그는 데코레이터가 담당합니다. `[LOG] save 실행`은 저장을 시작했다는 뜻이며 저장 성공을 보장하는 메시지는 아닙니다.

### 실제 코드: 실행 시간 측정

`time_action`은 함수 호출 전 시간을 기록하고, 함수가 끝난 뒤 경과 시간을 출력합니다.

```python
from budget_app.decorators import time_action

@time_action
def calculate_expense():
    return sum([1000, 2000, 3000])

print(calculate_expense())
```

stdout:

```text
6000
```

stderr 예시:

```text
[TIME] calculate_expense: 0.0000s
```

측정값은 실행마다 달라집니다. 현재 구현은 `try/finally`를 사용하므로 함수가 성공하거나 예외로 끝나더라도 시간 측정 메시지를 출력합니다.

가계부에서는 `handle_search()`와 `handle_summary()`에 적용해 검색·요약 handler 전체의 시간을 측정합니다.

### 실제 코드: 예외를 사용자 안내로 바꾸기

`handle_errors`는 처리 대상 예외를 잡고 원인·힌트를 출력한 뒤 실패 코드를 반환합니다.

```python
from budget_app.decorators import handle_errors
from budget_app.validators import parse_amount

@handle_errors
def example_command():
    print("금액 검증 시작")
    parse_amount("1,000")
    print("금액 검증 완료")
    return 0

result = example_command()
print("반환 코드:", result)
```

stdout:

```text
금액 검증 시작
반환 코드: 1
```

stderr:

```text
[오류] 잘못된 데이터: 금액은 쉼표 없는 정수로 입력하세요. 예: 1000
[힌트] 입력값을 확인하세요.
```

실행 흐름은 다음과 같습니다.

1. `parse_amount("1,000")`에서 `ValueError`가 발생합니다.
2. 원래 함수의 실행이 중단되므로 `금액 검증 완료`는 출력하지 않습니다.
3. 바깥의 `handle_errors`가 해당 예외를 받아 안내하고 1을 반환합니다.

데코레이터가 오류를 처리해도 함수의 중단된 위치부터 다시 실행하는 것은 아닙니다. 잘못된 입력을 자동으로 다시 받는 기능도 아닙니다.

현재 프로젝트에서는 `@handle_errors`를 `main()`에 적용하고, [__main__.py](../budget_app/__main__.py)의 `raise SystemExit(main())`이 반환값을 실제 프로세스 종료 코드로 전달합니다. 위 학습 예시는 반환값만 출력하므로 예시 Python 프로세스 자체를 종료 코드 1로 끝내지는 않습니다.

stderr는 메시지의 출력 위치입니다. stderr로 출력한다는 사실만으로 실패 코드가 되는 것은 아닙니다. 또한 현재 데코레이터는 지정한 예외를 처리하며 모든 종류의 예외를 무조건 숨기지는 않습니다.

## 3. 제너레이터와 데코레이터를 함께 이해하기

### 제너레이터의 실제 실행 시점과 시간 측정

제너레이터 함수는 호출할 때 본문이 실행되지 않습니다. 따라서 일반적인 `time_action`을 제너레이터 함수 자체에 붙이면, 값을 모두 읽는 시간이 아니라 제너레이터 객체를 만드는 시간만 측정하게 됩니다.

현재 가계부에서는 실제 거래를 순회하는 `handle_search()`·`handle_summary()`에 시간 측정을 적용했습니다. 이 함수들이 끝날 때까지 기다리므로 해당 handler 안에서 수행한 파일 읽기·검색·출력 등을 포함합니다.

### atomic_write(): yield와 contextmanager의 결합

[repository.py](../budget_app/repository.py)의 `atomic_write()`는 `yield`를 사용하면서 `@contextmanager`가 적용되어 있습니다. 이 데코레이터는 제너레이터를 `with`문에서 사용할 수 있도록 바꿉니다.

먼저 파일 처리 없이 실행 순서만 확인해 볼 수 있습니다.

```python
from contextlib import contextmanager

@contextmanager
def managed_resource():
    print("준비")
    try:
        yield "사용할 자원"
    finally:
        print("정리")

with managed_resource() as resource:
    print("사용:", resource)
```

출력:

```text
준비
사용: 사용할 자원
정리
```

`with`에 진입할 때는 `yield`까지 실행하고, 전달한 값이 `resource`에 들어갑니다. `with` 블록이 끝나면 `yield` 다음 부분을 실행하며, 예외가 발생해도 `finally`로 정리합니다.

가계부에서는 이 구조가 다음처럼 사용됩니다.

```text
with 진입
    → 임시 파일 생성
    → yield dest: 쓸 파일을 with 블록에 전달
    → with 블록에서 데이터 기록
정상 종료
    → flush·fsync·파일 닫기
    → os.replace로 원본 교체
    → 임시 파일 정리
블록 안에서 오류 발생
    → yield 위치로 예외 전달
    → 원본 교체 단계는 실행하지 않음
    → finally에서 임시 파일 정리
```

일반 거래 읽기의 `yield`는 다음 레코드를 순차 전달하는 데 사용하고, `atomic_write()`의 `yield`는 `with` 블록 전후의 준비·저장·정리 시점을 나누는 데 사용합니다.

## 4. 프로젝트에서 설명할 수 있어야 할 내용

| 개념 | 이 프로젝트에 적용한 이유 |
|---|---|
| 제너레이터 | 전체 거래를 한 번에 모으지 않고 파일 읽기·검색·일괄 저장을 연결하기 위해 |
| 최신순 선택 | 모든 거래를 확인하면서도 출력 개수에 비례하는 거래만 보관하기 위해 |
| 로그 데코레이터 | 저장·수정·삭제 함수마다 실행 로그 코드를 반복하지 않기 위해 |
| 시간 데코레이터 | 검색·요약 로직과 소요 시간 측정을 분리하기 위해 |
| 예외 데코레이터 | 일반 CLI 명령의 오류 안내 형식과 반환 코드를 공통 처리하기 위해 |
| contextmanager | 임시 파일의 준비·사용·정리 흐름을 한 함수에서 관리하기 위해 |

메모리와 시간에 대한 설명은 코드 구조에 따른 것이며, 대용량 파일을 실측한 수치는 제시하지 않습니다. 처리 비용과 향후 개선 방향은 [README의 성능 설명](README.md#7-스트리밍과-대용량-처리)을 참고하세요.
