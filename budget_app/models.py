from dataclasses import dataclass, field

                    #클래스의 생성자(__init__), 출력 함수(__repr__), 
@dataclass          #비교 함수(__eq__) 등을 자동으로 만들어 주는 데코레이터
class Transaction:
    id: str
    date: str
    type: str
    category: str
    amount: int
    memo: str = ""
    tags: list[str] = field(default_factory=list)