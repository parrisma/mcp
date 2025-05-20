# pylint: disable=C0114
# pylint: disable=C0115
# pylint: disable=C0116
# pylint: disable=C0103
# pylint: disable=C0301
"""
MCP Server - Model Context Protocol Server Implementation
This server provides tools and resources for AI models to use.

npx @modelcontextprotocol/inspector python ./mcp-server.py 
"""

# pylint: disable=W1203

import argparse
import logging
import os
import signal
import sys
import time
import types
from typing import Any, Dict, Literal, Optional

from langchain.prompts import PromptTemplate
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("mcp-server")


def parse_arguments():
    # Get default values from environment variables or use fallbacks
    default_host = os.environ.get("MCP_HOST", "127.0.0.1")
    default_port = int(os.environ.get("MCP_PORT", "6277"))

    parser = argparse.ArgumentParser(description="MCP Server")
    parser.add_argument("--host", default=default_host,
                        help=f"Host to bind the server to (default: {default_host}, env: MCP_HOST)")
    parser.add_argument("--port", type=int, default=default_port,
                        help=f"Port to bind the server to (default: {default_port}, env: MCP_PORT)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug mode")
    return parser.parse_args()


class MCPServer:
    """
    MCP Server class that provides tools, resources, and prompts for AI models.
    """

    def __init__(self, name: str, host: str, port: int):
        """
        Initialize the MCP Server with the given configuration.

        Args:
            name: The name of the server
            host: The host to bind the server to
            port: The port to bind the server to
        """
        self.name = name
        self.host = host
        self.port = port
        self.mcp = FastMCP(name, host=host, port=port)

        # Register tools, resources, and prompts
        self._register_tools()
        self._register_resources()
        self._register_prompts()

    def _register_tools(self):
        self.mcp.tool(name="add",
                      description="Add two integers together",
                      annotations=ToolAnnotations(
                          title="Simple arithmetic add",
                          readOnlyHint=True))(self._add)
        self.mcp.tool(name="multiply",
                      description="Multiplt two integers together",
                      annotations=ToolAnnotations(
                          title="Simple arithmetic multiplication",
                          readOnlyHint=True))(self.multiply)

    def _register_resources(self):
        self.mcp.resource(uri="message://{name}",
                          name="message",
                          description="Generate a greeting message for a given name")(self.get_message)
        self.mcp.resource(uri="alive://",
                          name="alive",
                          description="Return server status and server timestamp")(self.alive)

    def _register_prompts(self):
        self.mcp.prompt(name="sme",
                        description="Get a subject matter expert prompt for a specific topic")(self.get_sme_prompt)

    def _add(self,
             a: int,
             b: int) -> int:
        logger.info(f"Adding {a} and {b}")
        return a + b

    def multiply(self, a: int, b: int) -> int:
        logger.info(f"Multiplying {a} and {b}")
        return a * b

    def get_message(self, name: str) -> str:
        logger.info(f"Generating message for {name}")
        return f"Greetings, {name}!"

    def alive(self) -> Dict[str, Any]:
        """
        Check if the server is alive.

        Returns:
            A dictionary with status information
        """
        logger.info("Received a still alive request")
        return {
            "status": "ok",
            "timestamp": int(time.time()),
            "version": "1.0.0"
        }

    def get_sme_prompt(self,
                       topic: Literal['coding', 'math', 'writing'],
                       subject: str) -> str:
        """
        Get a prompt for a specific topic.

        Args:
            topic: The topic for the prompt

        Returns:
            A prompt string
        """
        logger.info(f"Generating an SME prompt for topic: {topic}")

        prompts = {
            "coding": PromptTemplate.from_template("You are an expert programmer with deep knowledge of software development, please explain {subject}"),
            "math": PromptTemplate.from_template("You are a high school mathematics tutor, please explain {subject}"),
            "writing": PromptTemplate.from_template("You are a professional writer and editor with expertise in creative writing, please write a paragraph on {subject}")
        }

        # Default prompt if topic not found
        default_prompt = PromptTemplate.from_template(
            "You are a helpful assistant. Please provide information about {subject}")

        prompt_template = prompts.get(topic.lower(), default_prompt)
        return prompt_template.format(subject=subject)

    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(_sig: int, _frame: Optional[types.FrameType]) -> None:
            logger.info("Shutting down MCP server...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def run(self, transport: Literal['stdio', 'sse', 'streamable-http'] = "sse"):
        """
        Run the MCP server.

        Args:
            transport: The transport protocol to use (default: "sse")
                       Must be one of: 'stdio', 'sse', or 'streamable-http'
        """
        # Log server startup with source of configuration
        host_source = "environment variable" if "MCP_HOST" in os.environ else "default"
        port_source = "environment variable" if "MCP_PORT" in os.environ else "default"
        logger.info(
            f"Starting MCP server on {self.host}:{self.port} (host from {host_source}, port from {port_source})")

        self.setup_signal_handlers()

        try:
            # Run the MCP server
            self.mcp.run(transport=transport)
        except Exception as e:
            logger.error(f"Error running MCP server: {e}")
            sys.exit(1)


def main():
    """Main entry point for the MCP server"""
    # Parse command line arguments
    args = parse_arguments()

    # Configure logging level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    # Create and run the MCP server
    server = MCPServer("Demo", args.host, args.port)
    server.run()


if __name__ == "__main__":
    main()
