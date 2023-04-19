"""
Module for the Config class.
"""

from dataclasses import dataclass


@dataclass
class Config:
    """
    Dataclass for storing the application's runtime configuration.
    """
    period: int  # period in seconds
