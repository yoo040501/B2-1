import sys
import json
from functools import wraps
from time import perf_counter

def time_action(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = perf_counter()

        try:
            return func(*args, **kwargs)
        finally:
            elapsed = perf_counter() - start

            print(
                f"[TIME] {func.__name__}: {elapsed:.4f}s",
                file=sys.stderr
            )

    return wrapper

def log_action(func):
    @wraps(func) # 원본 함수의 이름과 문서 정보 등을 유지
    def wrapper(*args, **kwargs): #*args: 위치 인자들을 튜플로 받음, **kwargs: 키워드 인자들을 딕셔너리로 받음
        print(f"[LOG] {func.__name__} 실행", file=sys.stderr)

        result = func(*args, **kwargs) #원본 함수를 실제로 실행하는 부분

        return result

    return wrapper

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except json.JSONDecodeError:
            print("[오류] JSON 파일 형식이 잘못되었습니다.", file=sys.stderr)
            print("[힌트] 저장 파일을 확인하세요.", file=sys.stderr)

        except OSError as e:
            print(f"[오류] 파일 처리 실패: {e}", file=sys.stderr)
            print("[힌트] 파일 경로와 권한을 확인하세요.", file=sys.stderr)

        except ValueError as e:
            print(f"[오류] 잘못된 데이터: {e}", file=sys.stderr)
            print("[힌트] 입력값을 확인하세요.", file=sys.stderr)

        except (KeyboardInterrupt, EOFError):
            print("\n[오류] 입력이 중단되었습니다.", file=sys.stderr)
            return 130

        return 1

    return wrapper