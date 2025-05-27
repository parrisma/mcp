"""
MCP Server - Model Context Protocol Server Implementation
This server provides tools and resources for AI models to use.

npx @modelcontextprotocol/inspector python ./mcp-server.py 
"""

# pylint: disable=W1203

import argparse
import logging
import os
import signal  # Keep for runner's own signal handling if any, or remove if MCPServer handles all
import sys
from typing import Any, Optional
from pathlib import Path  # Keep for parse_arguments

from mcp_server import MCPServer
from network_utils import NetworkUtils


class MCPServerRunner:
    """
    MCPServerRunner is a simple command-line interface for running the MCPServer.
    It allows users to specify the host, port, and configuration file for the server.
    """

    def __init__(self) -> None:

        self.log: logging.Logger = logging.getLogger("mcp-server-runner")
        return

    def parse_arguments(self) -> argparse.Namespace:
        default_host = os.environ.get("MCP_HOST", "127.0.0.1")
        default_port = int(os.environ.get("MCP_PORT", "6277"))
        # Ensure default_config_dir is relative to the runner script's location or an absolute path
        # For simplicity, keeping it as "./" which means relative to CWD where runner is executed.
        default_config_dir: str | Path = os.environ.get("MCP_CONFIG_DIR", Path(
            __file__).parent.parent.parent / "config")  # Default to /mcp/config
        default_config_file: str = os.environ.get(
            "MCP_CONFIG_FILE", "mcp-server-config.json")

        parser = argparse.ArgumentParser(description="MCP Server Runner")
        parser.add_argument("--host", default=default_host,
                            help=f"Host to bind the server to (default: {default_host}, env: MCP_HOST)")
        parser.add_argument("--port", type=int, default=default_port,
                            help=f"Port to bind the server to (default: {default_port}, env: MCP_PORT)")
        parser.add_argument("--config-dir", type=Path, default=Path(default_config_dir),
                            help=f"Directory where config file is located (default: {default_config_dir}, env: MCP_CONFIG_DIR)")
        parser.add_argument("--config-file", type=Path, default=Path(default_config_file).name,  # Ensure only filename for config_file
                            help=f"Config file name (default: {default_config_file}, env: MCP_CONFIG_FILE)")
        parser.add_argument("--debug", action="store_true",
                            help="Enable debug mode")
        return parser.parse_args()

    def run(self) -> None:
        args: argparse.Namespace = self.parse_arguments()

        if args.debug:
            self.log.setLevel(logging.DEBUG)  # Set global log level
            self.log.debug("Debug mode enabled for runner.")

        # Signal handling for the runner itself (graceful shutdown of the runner)
        def runner_signal_handler(_sig: int, _frame: Optional[Any]) -> None:
            self.log.info(f"Received signal {_sig}. Initiating shutdown...")
            sys.exit(0)

        signal.signal(signal.SIGINT, runner_signal_handler)
        signal.signal(signal.SIGTERM, runner_signal_handler)

        try:
            # Ensure config_file is just the filename, config_dir is the directory path
            server_config_file_name = args.config_file if isinstance(
                args.config_file, str) else args.config_file.name

            server: MCPServer = MCPServer(name="MCP Demo Server",  # This name could also be from config or args
                                          host=args.host,
                                          port=args.port,
                                          config_dir=args.config_dir,
                                          config_file=Path(server_config_file_name))

            # The MCPServer's run method is blocking.
            server.run()

        except Exception as e:
            raise RuntimeError(
                f"Failed to start or run MCP server: {e}") from e


if __name__ == "__main__":
    MCPServerRunner().run()
