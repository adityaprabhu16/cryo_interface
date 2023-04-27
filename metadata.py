"""
Module for the Metadata class.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Metadata:
    """
    Dataclass for storing experimental metadata.
    """
    title: str
    name: str
    cpa: str
    date: str
    temp1: Optional[str]
    temp2: Optional[str]
    vna1: Optional[str]
    vna2: Optional[str]
    vna1_temp: Optional[str]
    vna2_temp: Optional[str]
