# DO NOT EDIT - AUTOMATICALLY GENERATED BY tests/make_test_stubs.py!
from typing import List
from pandas.core.frame import DataFrame
from typing import (
    List,
    Optional,
)


def Pt(CASRN: str, get_methods: bool = ..., method: Optional[str] = ...) -> Optional[float]: ...


def Pt_methods(CASRN: str) -> List[str]: ...


def Tt(CASRN: str, get_methods: bool = ..., method: Optional[str] = ...) -> Optional[float]: ...


def Tt_methods(CASRN: str) -> List[str]: ...


def __getattr__(name: str) -> DataFrame: ...


def _load_triple_data() -> None: ...

__all__: List[str]