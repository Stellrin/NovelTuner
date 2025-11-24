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
import tempfile
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

    def run_tool_chain(self, tool_chain: str, args: List[str]) -> int:
        """Run a chain of tools sequentially with intermediate file management"""
        # Parse tool chain (format: tool1+tool2+tool3)
        tool_names = [t.strip() for t in tool_chain.split('+')]

        # Validate all tools exist
        for tool_name in tool_names:
            if tool_name not in self.tools:
                print(f"Tool '{tool_name}' not found.")
                print("Available tools:", ", ".join(sorted(self.tools.keys())))
                return 1

        # Parse base arguments (input, output, etc.)
        try:
            # Find the first tool to use its parser for base argument parsing
            first_tool = self.tools[tool_names[0]]
            first_parser = first_tool.get_parser()

            # Temporarily modify parser to make input optional for parsing tool-specific args
            input_required = False
            for action in first_parser._actions:
                if hasattr(action, 'dest') and action.dest == 'input':
                    input_required = action.required
                    action.required = False
                    break

            parsed_base_args = first_parser.parse_known_args(args)[0]

            # Restore original required status
            for action in first_parser._actions:
                if hasattr(action, 'dest') and action.dest == 'input':
                    action.required = input_required
                    break

        except Exception as e:
            print(f"Error parsing base arguments: {e}")
            return 1

        # Get input path (required for chain processing)
        input_path = getattr(parsed_base_args, 'input', None)
        if not input_path:
            print("Error: Input path is required for tool chain processing")
            return 1

        # Get final output path (optional)
        final_output = getattr(parsed_base_args, 'output', None)

        # Create temporary directory for intermediate files
        temp_dir = Path(tempfile.mkdtemp(prefix="novel_tuner_"))
        try:
            if not parsed_base_args.quiet:
                print(f"Running tool chain: {' -> '.join(tool_names)}")
                print(f"Input: {input_path}")
                if final_output:
                    print(f"Final output: {final_output}")
                print(f"Temporary directory: {temp_dir}")
                print("-" * 50)

            # Process each tool in sequence
            current_input = input_path
            intermediate_files = []

            for i, tool_name in enumerate(tool_names):
                is_last_tool = (i == len(tool_names) - 1)
                tool = self.tools[tool_name]

                if not parsed_base_args.quiet:
                    print(f"\n[{i+1}/{len(tool_names)}] Running {tool_name}...")

                # Determine output for this step
                if is_last_tool and final_output:
                    # Last tool and output specified - use final output
                    step_output = final_output
                else:
                    # Create intermediate file
                    input_path_obj = Path(current_input)
                    if input_path_obj.is_file():
                        # Input is a file
                        ext = input_path_obj.suffix
                        step_output = str(temp_dir / f"step_{i+1}_{tool_name}{ext}")
                    else:
                        # Input is a directory
                        step_output = str(temp_dir / f"output_step_{i+1}_{tool_name}")

                # Build arguments for this step
                step_args = [str(current_input), "-o", str(step_output)]

                # Add other common arguments from base args
                if parsed_base_args.recursive:
                    step_args.extend(["-r"])
                if parsed_base_args.backup:
                    step_args.extend(["-b"])
                if parsed_base_args.verbose:
                    step_args.extend(["-v"])
                if parsed_base_args.quiet:
                    step_args.extend(["-q"])

                # Add tool-specific arguments (filter out base args)
                tool_parser = tool.get_parser()
                base_arg_names = {'input', 'output', 'recursive', 'backup', 'verbose', 'quiet'}

                # Parse all args to separate tool-specific ones
                all_parsed_args, remaining_args = tool_parser.parse_known_args(args)

                # Add tool-specific args
                for action in tool_parser._actions:
                    if hasattr(action, 'dest'):
                        dest = action.dest
                        if dest not in base_arg_names and dest != 'help':
                            value = getattr(all_parsed_args, dest, None)
                            if value is not None:
                                # Skip default values for flags
                                if action.default != value:
                                    if isinstance(value, bool):
                                        if value:
                                            step_args.extend([action.option_strings[0]])
                                    elif isinstance(value, str):
                                        step_args.extend([action.option_strings[0], value])

                # Run the tool
                exit_code = self.run_tool(tool_name, step_args)

                if exit_code != 0:
                    print(f"Error: Tool '{tool_name}' failed with exit code {exit_code}")
                    return exit_code

                # Update input for next step
                if not is_last_tool or not final_output:
                    intermediate_files.append(step_output)
                current_input = step_output

                if not parsed_base_args.quiet:
                    print(f"[OK] {tool_name} completed")

            if not parsed_base_args.quiet:
                print("\n" + "-" * 50)
                print(f"Tool chain completed successfully!")
                if final_output:
                    print(f"Final output: {final_output}")
                else:
                    print(f"Final output: {current_input}")

            return 0

        finally:
            # Clean up intermediate files unless --keep-intermediate is set
            if not getattr(parsed_base_args, 'keep_intermediate', False):
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    if not parsed_base_args.quiet:
                        print(f"Warning: Failed to clean up temp directory: {e}")
            else:
                if not parsed_base_args.quiet:
                    print(f"\nIntermediate files kept in: {temp_dir}")

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
  python novel_tuner.py fix_line_breaks+traditional_to_simplified input.txt -o output.txt
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
        tool_name_or_chain = sys.argv[1]

        # Handle --help for specific tool
        if len(sys.argv) > 2 and sys.argv[2] == "--help":
            return tool_manager.get_tool_help(tool_name_or_chain)

        # Check if this is a tool chain (contains +)
        if '+' in tool_name_or_chain:
            # Run tool chain
            tool_args = sys.argv[2:]
            return tool_manager.run_tool_chain(tool_name_or_chain, tool_args)
        else:
            # Run single tool
            tool_args = sys.argv[2:]
            return tool_manager.run_tool(tool_name_or_chain, tool_args)

    # Default behavior: show main help
    main_parser = create_main_parser()
    main_parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())