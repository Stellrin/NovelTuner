"""
NovelTuner Tools Package
Text processing tools for novel editing and conversion
"""

# This package contains all the text processing tools
# Each tool must implement the standard interface:
# - get_description() -> str
# - get_parser() -> ArgumentParser
# - main(args) -> int (return code)