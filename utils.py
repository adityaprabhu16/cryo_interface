"""
Utility functions used in various places throughout the program.
"""

import dataclasses
import glob
import json
import os
import sys
from typing import List

import serial


class EnhancedJSONEncoder(json.JSONEncoder):
    """
    From https://stackoverflow.com/questions/51286748/make-the-python-json-encoder-support-pythons-new-dataclasses
    """
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def find_available_devices() -> List[str]:
    """
    Lists serial port names.
    Based off of: https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python

    :raises EnvironmentError: On unsupported or unknown platforms
    :returns: A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result: List[str] = []
    for port in ports:
        s = None
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except Exception:
            if s:
                s.close()
    return result


def find_previous_experiments() -> List[str]:
    """
    Find what previous experiments are available.
    
    :returns: List of directories (experiment names)
    """
    return next(os.walk('experiments/'))[1]
