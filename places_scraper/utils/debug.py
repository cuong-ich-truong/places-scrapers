"""Debug utility functions."""

from datetime import datetime
from typing import Any
import traceback
import sys


def debug(func_name: str, obj: Any) -> None:
    """Print debug information with timestamp and stack trace.

    Args:
        func_name: Name of the function being debugged
        obj: Object to print debug information for
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp}] Debug in {func_name}:")
    print(f"Object type: {type(obj)}")
    print(f"Object content: {obj}")

    if isinstance(obj, TypeError):
        print("\nError stack trace:")
        print("".join(traceback.format_tb(obj.__traceback__)))
    elif isinstance(obj, RecursionError):
        print("\nRecursionError detected - printing last 10 frames:")
        print("".join(traceback.format_stack()[-10:]))
    else:
        print("\nCurrent stack trace:")
        traceback.print_stack()
