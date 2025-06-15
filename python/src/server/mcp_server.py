import logging
import os
import json
from enum import Enum
from re import I
from typing import Any, Literal, List, Callable, Tuple, Union
from functools import partial
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from network_utils import NetworkUtils
from i_mcp_server import IMCPServer


class MCPServer:
    logger: logging.Logger = logging.getLogger("mcp-server")

    class MCPServerDetail(str, Enum):
        NAME = "name"
        INSTRUNCTIONS = "instructions"
        VERSION = "version"

        def __str__(self) -> Literal['name', 'instructions', 'version']:
            return self.value

    class MCPServerCapabilityType(str, Enum):
        TOOLS = "tools"
        RESOURCES = "resources"
        RESOURCE_TEMPLATES = "resource_templates"
        PROMPTS = "prompts"

        def __str__(self) -> Literal['tools', 'resources', 'prompts', 'resource_templates']:
            return self.value

    class MCPServerToolMetaData(str, Enum):
        NAME = "name"
        DESCRIPTION = "description"
        TITLE = "annotations.title"
        READ_ONLY_HINT = "annotations.readOnlyHint"
        DESTRUCTIVE_HINT = "annotations.destructiveHint"
        IDEMPOTENT_HINT = "annotations.idempotentHint"
        OPEN_WORLD_HINT = "annotations.openWorldHint"

        def __str__(self) -> Literal['name', 'description', 'annotations.title', 'annotations.readOnlyHint', 'annotations.destructiveHint', 'annotations.idempotentHint', 'annotations.openWorldHint']:
            return self.value

    class MCPServerResourceMetaData(str, Enum):
        NAME = "name"
        DESCRIPTION = "description"
        TITLE = "annotations.title"
        URI = "uri"

        def __str__(self) -> Literal['name', 'description', 'annotations.title', 'uri']:
            return self.value

    class MCPServerPromptMetaData(str, Enum):
        NAME = "name"
        DESCRIPTION = "description"

        def __str__(self) -> Literal['name', 'description']:
            return self.value

    def __init__(self,
                 host: str,
                 port: int,
                 config_dir: Path,
                 config_file: Path,
                 server_instance: IMCPServer) -> None:

        self._host: str = host
        self._port: int = port
        self._config_dir: Path = config_dir
        self._config_file_path: Path
        self._server: IMCPServer = server_instance

        self.logger.info("Creating MCPServer Instance")

        if not isinstance(self._port, int) or not (0 < self._port < 65536):
            raise ValueError(
                f"Invalid port: [{self._port}]. Port must be an integer between 1 and 65535")

        if not NetworkUtils.is_free_port(self._host, self._port):
            raise ValueError(
                f"Given Port {self._port} is not available to use on host {self._host}.")

        if not NetworkUtils.is_resolvable_hostname(self._host):
            raise ValueError(
                f"Invalid host: [{self._host}]. Hostname could not be resolved.")

        self.logger.info(f"MCPServer using working directory: [{os.getcwd()}]")

        try:
            self._config_file_path = Path(
                config_dir) / Path(config_file)
            if not self._config_file_path.is_file():
                raise ValueError(
                    f"Config file does not exist: [{self._config_file_path}]")
            with open(self._config_file_path, "r", encoding="utf-8") as f:
                self._meta = json.load(f)
                self.logger.info(
                    f"configuration loaded from: '[{self._config_file_path}]'")
        except Exception as e:
            # Log the path that was attempted
            msg: str = f"Error loading metadata from config file: [{self._config_file_path}]"
            self.logger.error(msg, exc_info=True)
            raise ValueError(msg) from e

        self.logger.info(
            f"MCP Server to be created with name'[{self._server.server_name}]'")
        self.logger.info(f"host: '[{self._host}]'")
        self.logger.info(f"port: [{self._port}]")

        self._mcp = FastMCP(name=self._meta[MCPServer.MCPServerDetail.NAME],
                            instructions=self._meta[MCPServer.MCPServerDetail.INSTRUNCTIONS],
                            host=self._host,
                            port=self._port)
        self.logger.info("MCP Server instance created")

        self._register_tools(self._server.supported_tools)
        self._register_resources(self._server.supported_resources)
        self._register_prompts(self._server.supported_prompts)
        self.logger.info("MCP Server instanc fully initialized")

    def _get_meta(self,
                  meta_type: Union['MCPServer.MCPServerCapabilityType', str],
                  name: str,
                  item_path: Union['MCPServer.MCPServerToolMetaData', 'MCPServer.MCPServerResourceMetaData', 'MCPServer.MCPServerPromptMetaData', str]) -> Any:
        try:
            # Ensure meta_type and item_path are strings if they are Enum members
            meta_type_str = str(meta_type)
            item_path_str = str(item_path)

            keys = [meta_type_str, name]
            if "." in item_path_str:
                keys.extend(item_path_str.split("."))
            else:
                keys.append(item_path_str)

            value = self._meta
            current_path_for_error = ""
            for k_idx, k_val in enumerate(keys):
                # First two keys (meta_type_str, name) are direct lookups in the structure like self._meta['tools']['add']
                # Subsequent keys from item_path_str navigate within that specific tool/resource/prompt's dict.
                if k_idx == 0:  # meta_type_str
                    current_path_for_error = f"['{k_val}']"
                    if k_val not in value:
                        raise KeyError(f"Meta type key '{k_val}' not found.")
                    value = value[k_val]
                elif k_idx == 1:  # name (e.g. 'add')
                    current_path_for_error += f"['{k_val}']"
                    if k_val not in value:
                        raise KeyError(
                            f"Item name key '{k_val}' not found under '{keys[0]}'.")
                    value = value[k_val]
                else:  # keys from item_path
                    current_path_for_error += f"['{k_val}']"
                    # Check if value is a dict before key access
                    if not isinstance(value, dict) or k_val not in value:
                        raise KeyError(
                            f"Key '{k_val}' not found at path {current_path_for_error}.")
                    value = value[k_val]
            return value
        except KeyError as ke_original:
            full_path_str = f"{str(meta_type)} -> {name} -> {str(item_path)}"
            raise ValueError(
                f"Metadata not found for {full_path_str}. Details: {str(ke_original)}") from ke_original

    def _register_tools(self,
                        tools_to_add: List[Tuple[str, Callable]]) -> None:
        self.logger.info("MCP Server Registering tools started")
        for tool_name, tool_func in tools_to_add:
            try:
                get_meta = partial(
                    self._get_meta, MCPServer.MCPServerCapabilityType.TOOLS, tool_name)
                self._mcp.tool(
                    name=get_meta(MCPServer.MCPServerToolMetaData.NAME),
                    description=get_meta(
                        MCPServer.MCPServerToolMetaData.DESCRIPTION),
                    annotations=ToolAnnotations(
                        title=get_meta(MCPServer.MCPServerToolMetaData.TITLE),
                        readOnlyHint=get_meta(
                            MCPServer.MCPServerToolMetaData.READ_ONLY_HINT),
                        destructiveHint=get_meta(
                            MCPServer.MCPServerToolMetaData.DESTRUCTIVE_HINT),
                        idempotentHint=get_meta(
                            MCPServer.MCPServerToolMetaData.IDEMPOTENT_HINT),
                        openWorldHint=get_meta(
                            MCPServer.MCPServerToolMetaData.OPEN_WORLD_HINT),
                    ),
                )(tool_func)
                self.logger.info(f"Tool [{tool_name}] registered")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to register tool [{tool_name}]: {e}") from e
        self.logger.info("MCP Server Registering tools completed")

    def _register_resources(self,
                            resources_to_add: List[Tuple[str, Callable]]) -> None:
        self.logger.info("MCP Server Registering resources started")
        for resource_name, resource_func in resources_to_add:
            try:
                get_meta = partial(
                    self._get_meta, MCPServer.MCPServerCapabilityType.RESOURCES, resource_name)
                self._mcp.resource(
                    uri=get_meta(MCPServer.MCPServerResourceMetaData.URI),
                    name=get_meta(MCPServer.MCPServerResourceMetaData.NAME),
                    description=get_meta(
                        MCPServer.MCPServerResourceMetaData.DESCRIPTION)
                )(resource_func)
                self.logger.info(f"Resource [{resource_name}] registered")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to register resource [{resource_name}]: {e}") from e
        self.logger.info("MCP Server Registering resources completed")

    def _register_prompts(self,
                          prompts_to_add: List[Tuple[str, Callable]]) -> None:

        self.logger.info("MCP Server Registering prompts started")
        for prompt_name, prompt_func in prompts_to_add:
            try:
                get_meta = partial(
                    self._get_meta, MCPServer.MCPServerCapabilityType.PROMPTS, prompt_name)
                self._mcp.prompt(
                    name=get_meta(MCPServer.MCPServerPromptMetaData.NAME),
                    description=get_meta(
                        MCPServer.MCPServerPromptMetaData.DESCRIPTION)
                )(prompt_func)
                self.logger.info(f"Prompt [{prompt_name}] registered")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to register prompt [{prompt_name}]: {e}") from e
        self.logger.info("MCP Server Registering prompts completed")

    def run(self,
            transport: Literal['stdio', 'sse', 'streamable-http'] = "sse"):

        self.logger.info(
            f"Running MCP server '{self._server.server_name}' on {self._host}:{self._port}")
        try:
            self._mcp.run(transport=transport)
            self.logger.info(
                f"Exited MCP server '{self._server.server_name}' on {self._host}:{self._port}")
        except Exception as e:
            raise RuntimeError(
                f"Error running MCP server '{self._server.server_name}': {e}") from e


if __name__ == "__main__":
    print("Error: This module must be run using the mcp_server_runner.py script.", flush=True)
    exit(1)
