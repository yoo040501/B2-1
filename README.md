# CLI 가계부 프로그램

Python 표준 라이브러리로 구현한 터미널 기반 가계부 프로그램입니다.

거래 내역을 JSONL 파일에 저장하고, 거래 관리, 검색, 월별 통계, 예산 및 카테고리 관리, CSV 입출력 기능을 제공합니다.

## 1. 실행 환경

- Python 3.10 이상
- 외부 패키지 설치 불필요
- Python 표준 라이브러리만 사용

프로젝트 최상위 디렉터리에서 실행합니다.

```bash
python3 -m budget_app --help
```

## 2. 주요 기능

- 거래 추가, 조회, 검색, 수정, 삭제
- 날짜·카테고리·거래 유형·메모·태그 기반 검색
- 월별 수입·지출·잔액 및 카테고리별 지출 통계
- 월별 예산 설정 및 초과 경고
- 카테고리 추가·조회·삭제
- CSV 파일 가져오기 및 내보내기
- 사용자 입력 검증 및 예외 처리
- JSONL 기반 영구 저장

## 3. 사용 방법

**거래 추가**

```bash
python3 -m budget_app add
```

**최근 거래 조회**

```bash
python3 -m budget_app list --limit 10
```

**거래 검색**

```bash
python3 -m budget_app search --category food
python3 -m budget_app search --type expense
python3 -m budget_app search --q 점심
python3 -m budget_app search --from 2026-10-01 --to 2026-10-31
```

**월별 요약**

```bash
python3 -m budget_app summary --month 2026-10 --top 3
```

**예산 설정**

```bash
python3 -m budget_app budget set --month 2026-10 --amount 100000
```

**카테고리 관리**

```bash
python3 -m budget_app category list
python3 -m budget_app category add
python3 -m budget_app category remove
```

**거래 수정 및 삭제**

```bash
python3 -m budget_app update --id TX-001 --amount 20000
python3 -m budget_app delete --id TX-001
```

**CSV 내보내기 및 가져오기**

```bash
python3 -m budget_app export --out export.csv --month 2026-10
python3 -m budget_app import --from import.csv
```

**데이터 저장 폴더 변경**

```bash
python3 -m budget_app --data-dir test_data list
```

## 4. 데이터 저장 방식

기본 저장 디렉터리는 `data/`입니다.

- `transactions.jsonl`: 거래 내역
- `categories.jsonl`: 카테고리 목록
- `budgets.jsonl`: 월별 예산

JSONL 형식을 사용해 데이터를 파일에 영구 저장하며, 거래 조회에는 제너레이터를 활용합니다.

거래 ID는 `TX-001` 형식으로 생성됩니다.

CSV 파일은 다음 열을 사용합니다.

`date,type,category,amount,memo,tags`

## 5. 프로젝트 구조

- `cli.py`: 명령어 실행 분기
- `parser.py`: argparse 기반 명령어·옵션 정의
- `commands/`: 명령어별 입력·출력 및 처리
- `models.py`: 거래 데이터 모델
- `repository.py`: JSONL 데이터 저장·조회·수정
- `service.py`: 검색·통계 및 카테고리 복구
- `csv_io.py`: CSV 입출력
- `validators.py`: 입력값 검증
- `decorators.py`: 로깅 및 예외 처리
- `tests/`: 자동 테스트

## 6. 데이터 무결성 및 예외 처리

- 잘못된 날짜, 거래 유형 및 금액 입력을 검증합니다.
- 거래에서 사용 중인 카테고리는 명령어로 삭제할 수 없습니다.
- 저장된 거래에서 사용하는 카테고리가 목록에 없으면 자동으로 복구합니다.
- 저장 파일 교체가 필요한 작업에는 임시 파일과 원자적 교체 방식을 사용합니다.
- 오류 발생 시 사용자에게 메시지를 출력하고 0이 아닌 종료 코드를 반환합니다.

CSV 파일을 반복해서 가져오면 동일한 내용의 거래가 중복 저장될 수 있습니다. 또한 데이터 파일을 직접 수정하면 데이터 일관성이 깨질 수 있습니다.
