#!/usr/bin/env python3
"""
NovelTuner - Unified Management System
Main entry point for all text processing tools
"""

import os
import sys
import argparse
import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Any


class ToolManager:
    """Manages all available tools and provides unified access"""

    def __init__(self):
        self.tools_dir = Path(__file__).parent / "tools"
        self.tools: Dict[str, Any] = {}
        self.discover_tools()

    def discover_tools(self) -> None:
        """Automatically discover all tools in the tools directory"""
        if not self.tools_dir.exists():
            print(f"Warning: Tools directory '{self.tools_dir}' not found")
            return

        # Add tools directory to Python path
        tools_path = str(self.tools_dir)
        if tools_path not in sys.path:
            sys.path.insert(0, tools_path)

        # Scan for Python files in tools directory
        for tool_file in self.tools_dir.glob("*.py"):
            if tool_file.name.startswith("__"):
                continue

            tool_name = tool_file.stem
            try:
                # Clear any existing module from cache
                if tool_name in sys.modules:
                    del sys.modules[tool_name]

                # Import the module
                spec = importlib.util.spec_from_file_location(tool_name, tool_file)
                if spec is None:
                    print(f"Warning: Could not create spec for '{tool_name}'")
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Check if it has the required interface
                has_description = hasattr(module, 'get_description')
                has_parser = hasattr(module, 'get_parser')
                has_main = hasattr(module, 'main')

                if has_description and has_parser and has_main:
                    self.tools[tool_name] = module
                    print(f"Discovered tool: {tool_name}")
                else:
                    missing = []
                    if not has_description: missing.append("get_description")
                    if not has_parser: missing.append("get_parser")
                    if not has_main: missing.append("main")
                    print(f"Warning: Tool '{tool_name}' missing required functions: {', '.join(missing)}")

            except Exception as e:
                print(f"Error loading tool '{tool_name}': {e}")
                import traceback
                traceback.print_exc()

    def list_tools(self) -> None:
        """List all available tools with descriptions"""
        if not self.tools:
            print("No tools available.")
            return

        print("Available tools:")
        print("-" * 50)

        for tool_name, module in sorted(self.tools.items()):
            try:
                description = module.get_description()
                print(f"  {tool_name:<20} - {description}")
            except Exception as e:
                print(f"  {tool_name:<20} - Error: {e}")

    def get_tool_help(self, tool_name: str) -> None:
        """Show help for a specific tool"""
        if tool_name not in self.tools:
            print(f"Tool '{tool_name}' not found.")
            print("Available tools:", ", ".join(sorted(self.tools.keys())))
            return 1

        try:
            parser = self.tools[tool_name].get_parser()
            parser.prog = f"novel_tuner.py {tool_name}"  # Update program name
            parser.print_help()
            return 0
        except Exception as e:
            print(f"Error getting help for tool '{tool_name}': {e}")
            return 1

    def run_tool(self, tool_name: str, args: List[str]) -> int:
        """Run a specific tool with given arguments"""
        if tool_name not in self.tools:
            print(f"Tool '{tool_name}' not found.")
            print("Available tools:", ", ".join(sorted(self.tools.keys())))
            return 1

        try:
            # Get the tool's argument parser
            parser = self.tools[tool_name].get_parser()

            # Parse arguments
            parsed_args = parser.parse_args(args)

            # Run the tool
            return self.tools[tool_name].main(parsed_args)

        except SystemExit as e:
            # argparse calls sys.exit() on help or error
            return e.code if e.code is not None else 1
        except Exception as e:
            print(f"Error running tool '{tool_name}': {e}")
            return 1


def create_main_parser() -> argparse.ArgumentParser:
    """Create the main argument parser"""
    parser = argparse.ArgumentParser(
        prog="novel_tuner",
        description="NovelTuner - Unified text processing tools for novels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python novel_tuner.py --list-tools
  python novel_tuner.py fix_line_breaks input.txt -o output.txt
  python novel_tuner.py image_fixer --help
        """
    )

    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="List all available tools"
    )

    return parser


def main() -> int:
    """Main entry point"""
    # Create tool manager
    tool_manager = ToolManager()

    # Quick check for --list-tools (no tool discovery needed)
    if len(sys.argv) == 2 and sys.argv[1] == "--list-tools":
        tool_manager.list_tools()
        return 0

    # Check if first argument looks like a tool name (no dash prefix)
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        tool_name = sys.argv[1]

        # Handle --help for specific tool
        if len(sys.argv) > 2 and sys.argv[2] == "--help":
            return tool_manager.get_tool_help(tool_name)

        # Run the tool with remaining arguments
        tool_args = sys.argv[2:]
        return tool_manager.run_tool(tool_name, tool_args)

    # Default behavior: show main help
    main_parser = create_main_parser()
    main_parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())