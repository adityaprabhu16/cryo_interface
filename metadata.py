
from dataclasses import dataclass
from typing import Optional


@dataclass
class Metadata:
    name: str
    cpa: str
    date: str
    temp1: Optional[str]
    temp2: Optional[str]
    vna1: Optional[str]
    vna2: Optional[str]
