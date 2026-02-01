"""Result type for error handling"""
from dataclasses import dataclass
from typing import TypeVar, Generic, Union

T = TypeVar('T')
E = TypeVar('E')


@dataclass
class Ok(Generic[T]):
    """Success result containing a value"""
    value: T
    
    def is_ok(self) -> bool:
        return True
    
    def is_err(self) -> bool:
        return False


@dataclass
class Err(Generic[E]):
    """Error result containing an error"""
    error: E
    
    def is_ok(self) -> bool:
        return False
    
    def is_err(self) -> bool:
        return True


# Result type alias
Result = Union[Ok[T], Err[E]]
