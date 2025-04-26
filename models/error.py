from dataclasses import dataclass

NOT_FOUND_ERROR = 1
BAD_REQUEST = 2
INTERNAL_ERROR = 3

@dataclass
class BadResponse:
    message: str
    code: int