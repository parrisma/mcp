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
import json
from enum import Enum
from typing import Any, Dict, Literal, Optional, Annotated, List, Callable, Tuple, Union
from functools import partial

from langchain.prompts import PromptTemplate
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field


# Define enums for metadata types and fields to avoid string literals
class MetaType(str, Enum):
    TOOLS = "tools"
    RESOURCES = "resources"
    PROMPTS = "prompts"

    def __str__(self):
        return self.value


class MetaField(str, Enum):
    NAME = "name"
    DESCRIPTION = "description"
    TITLE = "annotations.title"
    READ_ONLY_HINT = "annotations.readOnlyHint"
    DESTRUCTIVE_HINT = "annotations.destructiveHint"
    IDEMPOTENT_HINT = "annotations.idempotentHint"
    OPEN_WORLD_HINT = "annotations.openWorldHint"
    URI = "uri"
    URI_TEMPLATE = "uriTemplate"
    ARGUMENTS = "arguments"

    def __str__(self):
        return self.value


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

    def __init__(self, name: str,
                 host: str,
                 port: int,
                 in_conatiner: bool = False):
        """
        Initialize the MCP Server with the given configuration.

        Args:
            name: The name of the server
            host: The host to bind the server to
            port: The port to bind the server to
        """
        self._name = name
        self._host = host
        self._port = port
        self._mcp = FastMCP(self._name, host=self._host, port=self._port)

        meta_path: str = ""
        try:
            config_file = "mcp-server-config.json"
            if not in_conatiner:
                config_file = f"config/{config_file}"
            meta_path = os.path.join(
                os.getcwd(), config_file)
            with open(meta_path, "r", encoding="utf-8") as f:
                self._meta = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load or parse [{meta_path}]: {e}")
            raise RuntimeError(
                f"Aborting MCPServer initialization due to metadata file load error: [{meta_path}]") from e

        # Register tools, resources, and prompts
        self._register_tools()
        self._register_resources()
        self._register_prompts()

    def get_meta(self,
                 meta_type: Union[MetaType, Literal["tools", "resources", "prompts"]],
                 name: str,
                 item_path: Union[MetaField, str]) -> Any:
        """
        Retrieve a metadata item from the loaded _meta dictionary.

        Args:
            meta_type: The type of metadata (MetaType.TOOLS, MetaType.RESOURCES, or MetaType.PROMPTS)
            name: The name of the item (e.g., tool name)
            item_path: The specific metadata key or dot-separated path to retrieve (e.g., MetaField.DESCRIPTION or "arguments.type")

        Returns:
            The requested metadata value.

        Raises:
            RuntimeError: If the metadata item is not found.
        """
        try:
            # Support arbitrary depth using a JSON path (dot-separated)
            keys = [str(meta_type), name, str(item_path)] if isinstance(
                item_path, (MetaField, str)) else [str(meta_type), name]
            # If item is a dot-separated path, split and extend
            if isinstance(item_path, str) and "." in item_path:
                keys = [str(meta_type), name] + item_path.split(".")
            value = self._meta
            for k in keys:
                value = value[k]
            return value
        except KeyError as ke:
            raise RuntimeError(
                f"Metadata not found for type '{meta_type}', name '{name}', item '{item_path}'"
            ) from ke

    def _register_tools(self):
        # Register the add tool with fully qualified metadata
        # Get tool metadata using the config manager

        tools_to_add: List[Tuple[str, Callable]] = [
            ("add", self._add),
            ("multiply", self.multiply),
        ]

        for tool in tools_to_add:
            tool_name, tool_func = tool
            try:
                get_meta = partial(self.get_meta, MetaType.TOOLS, tool_name)
                self._mcp.tool(
                    name=get_meta(MetaField.NAME),
                    description=get_meta(MetaField.DESCRIPTION),
                    annotations=ToolAnnotations(
                        title=get_meta(MetaField.TITLE),
                        readOnlyHint=get_meta(MetaField.READ_ONLY_HINT),
                        destructiveHint=get_meta(MetaField.DESTRUCTIVE_HINT),
                        idempotentHint=get_meta(MetaField.IDEMPOTENT_HINT),
                        openWorldHint=get_meta(MetaField.OPEN_WORLD_HINT),
                    ),
                )(tool_func)
            except RuntimeError as e:
                msg = f"Failed to register tool [{tool_name}]: {e}"
                logger.error(msg)
                raise RuntimeError(msg) from e

    def _register_resources(self):
        resources_to_add = [
            ("message", self.get_message),
            ("alive", self.alive),
        ]

        for resource in resources_to_add:
            resource_name, resource_func = resource
            try:
                get_meta = partial(
                    self.get_meta, MetaType.RESOURCES, resource_name)
                self._mcp.resource(
                    uri=get_meta(MetaField.URI),
                    name=resource_name,
                    description=get_meta(MetaField.DESCRIPTION)
                )(resource_func)
            except RuntimeError as e:
                msg = f"Failed to register resource [{resource_name}]: {e}"
                logger.error(msg)
                raise RuntimeError(msg) from e

    def _register_prompts(self):
        prompts_to_add = [
            ("sme", self.get_sme_prompt),
        ]

        for prompt in prompts_to_add:
            prompt_name, prompt_func = prompt
            try:
                get_meta = partial(
                    self.get_meta, MetaType.PROMPTS, prompt_name)
                self._mcp.prompt(
                    name=prompt_name,
                    description=get_meta(MetaField.DESCRIPTION)
                )(prompt_func)
            except RuntimeError as e:
                msg = f"Failed to register prompt [{prompt_name}]: {e}"
                logger.error(msg)
                raise RuntimeError(msg) from e

    def _add(self,
             a: Annotated[int, Field(description="First integer to add")],
             b: Annotated[int, Field(description="Second integer to add")]) -> int:
        """
        Add two integers together.

        This tool is fully qualified with metadata in the _register_tools method.
        The parameters are annotated with descriptions using Pydantic's Field.
        """

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

    def run(self,
            transport: Literal['stdio', 'sse', 'streamable-http'] = "sse"):
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
            f"Starting MCP server on {self._host}:{self._port} (host from {host_source}, port from {port_source})")

        self.setup_signal_handlers()

        try:
            # Run the MCP server
            self._mcp.run(transport=transport)
        except Exception as e:
            logger.error(f"Error running MCP server: {e}")
            sys.exit(1)


def main():

    # Parse command line arguments
    args = parse_arguments()

    # Configure logging level based on debug flag
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    # Create and run the MCP server
    server = MCPServer("MCP Demo Server",
                       host=args.host,
                       port=args.port,
                       in_conatiner=True)
    server.run()


if __name__ == "__main__":
    main()
