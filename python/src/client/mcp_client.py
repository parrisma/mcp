# pylint: disable=C0301

import asyncio
from calendar import c
import logging
from enum import Enum
from typing import List, Dict, Any, Optional, Union, Literal
from h11 import SERVER
import mcp.types as types
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client


class MCPClient:
    """
    A client to connect to MCP servers and retrieve their capabilities.
    """
    class FailedToGetMCPServerCapabilities(Exception):
        pass

    class MCPServerCapabilities(str, Enum):
        SERVER_DETAIL = "server_detail"
        TOOLS = "tools"
        RESOURCES = "resources"
        RESOURCE_TEMPLATES = "resource_templates"
        PROMPTS = "prompts"

        def __str__(self) -> Literal['server_detail', 'tools', 'resources', 'resource_templates', 'prompts', 'server_url']:
            return self.value

    class MCPServerDetail(str, Enum):
        SERVER_URL = "server_url"
        NAME = "name"
        INSTRUCTIONS = "instructions"
        VERSION = "version"

        def __str__(self) -> Literal['name', 'instructions', 'version', 'server_url']:
            return self.value

    def __init__(self, server_base_urls: List[str]):
        if not server_base_urls:
            raise ValueError("At least one server base URL must be provided.")
        self.server_base_urls: List[str] = server_base_urls
        self.log: logging.Logger = logging.getLogger(
            __name__)  # Added logger instance
        # Configure basic logging if no handlers are already set for the root logger
        # This helps ensure logs are visible if the calling application hasn't configured logging
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler()]
            )

    async def __aenter__(self) -> "MCPClient":
        self.log.debug("MCPClient entering async context.")
        # Perform any setup if needed, though for this client,
        # connections are typically established per-method call.
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self.log.debug("MCPClient exiting async context.")
        # Perform any cleanup if needed.
        # If an exception occurred, it will be passed here.
        # Return False (or nothing, which defaults to False) to re-raise the exception.
        # Return True to suppress the exception (generally not recommended unless handled).
        pass

    async def get_server_capabilities(self, server_base_url: str) -> Dict[str, Any]:
        sse_url: str = f"{server_base_url.rstrip('/')}/sse"
        self.log.info(f"Attempting to connect to MCP server at: {sse_url}")

        capabilities: Dict[str, Any] = {}
        capabilities[MCPClient.MCPServerCapabilities.SERVER_DETAIL.value] = {}
        capabilities[MCPClient.MCPServerCapabilities.TOOLS.value] = []
        capabilities[MCPClient.MCPServerCapabilities.RESOURCES.value] = []
        capabilities[MCPClient.MCPServerCapabilities.RESOURCE_TEMPLATES.value] = []
        capabilities[MCPClient.MCPServerCapabilities.PROMPTS.value] = []

        try:
            async with sse_client(sse_url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    initialize_result: types.InitializeResult = await session.initialize()
                    await asyncio.sleep(1)

                    self.log.info(
                        f"Successfully connected to {sse_url}. Fetching capabilities...")

                    capabilities[MCPClient.MCPServerCapabilities.SERVER_DETAIL.value][
                        MCPClient.MCPServerDetail.SERVER_URL.value] = server_base_url
                    capabilities[MCPClient.MCPServerCapabilities.SERVER_DETAIL.value][
                        MCPClient.MCPServerDetail.NAME.value] = initialize_result.serverInfo.name
                    capabilities[MCPClient.MCPServerCapabilities.SERVER_DETAIL.value][
                        MCPClient.MCPServerDetail.INSTRUCTIONS.value] = initialize_result.instructions
                    capabilities[MCPClient.MCPServerCapabilities.SERVER_DETAIL.value][
                        MCPClient.MCPServerDetail.VERSION.value] = initialize_result.serverInfo.version

                    list_tools_result: types.ListToolsResult = await session.list_tools()
                    if list_tools_result and list_tools_result.tools:
                        for tool in list_tools_result.tools:
                            capabilities[MCPClient.MCPServerCapabilities.TOOLS.value].append(
                                self._format_tool(tool))

                    list_resources_result: types.ListResourcesResult = await session.list_resources()
                    if list_resources_result and list_resources_result.resources:
                        for resource in list_resources_result.resources:
                            capabilities[MCPClient.MCPServerCapabilities.RESOURCES.value].append(
                                self._format_resource(resource))

                    list_resource_templates_result: types.ListResourceTemplatesResult = await session.list_resource_templates()
                    if list_resource_templates_result and list_resource_templates_result.resourceTemplates:
                        for rt in list_resource_templates_result.resourceTemplates:
                            capabilities[MCPClient.MCPServerCapabilities.RESOURCE_TEMPLATES.value].append(
                                self._format_resource_template(rt))

                    list_prompts_result: types.ListPromptsResult = await session.list_prompts()
                    if list_prompts_result and list_prompts_result.prompts:
                        for prompt in list_prompts_result.prompts:
                            capabilities[MCPClient.MCPServerCapabilities.PROMPTS.value].append(
                                self._format_prompt(prompt))
            return capabilities
        except ConnectionRefusedError as ce:
            raise MCPClient.FailedToGetMCPServerCapabilities(
                f"Connection refused when trying to connect to {sse_url}. Is the server running?") from ce
        except asyncio.TimeoutError as te:
            raise MCPClient.FailedToGetMCPServerCapabilities(
                f"Timeout when trying to connect or communicate with {sse_url}.") from te
        except Exception as e:
            raise MCPClient.FailedToGetMCPServerCapabilities(
                f"Unable to get MCP capabilities for server at this address {server_base_url}: {e}"
            ) from e

    def _format_tool(self, tool: types.Tool) -> Dict[str, Any]:
        input_schema_data = tool.inputSchema if isinstance(
            tool.inputSchema, dict) else {}

        return {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": input_schema_data,
            "annotations": self._format_tool_annotations(tool.annotations) if tool.annotations else None
        }

    def _format_tool_annotations(self, annotations: types.ToolAnnotations) -> Dict[str, Any]:
        return {
            "title": annotations.title,
            "readOnlyHint": annotations.readOnlyHint,
            "destructiveHint": annotations.destructiveHint,
            "idempotentHint": annotations.idempotentHint,
            "openWorldHint": annotations.openWorldHint,
        }

    def _format_resource(self, resource: types.Resource) -> Dict[str, Any]:
        return {
            "name": resource.name,
            "uri": str(resource.uri),
            "description": resource.description,
        }

    def _format_resource_template(self, rt: types.ResourceTemplate) -> Dict[str, Any]:
        return {
            "name": rt.name,
            "uriTemplate": rt.uriTemplate,
            "description": rt.description,
        }

    def _format_prompt(self, prompt: types.Prompt) -> Dict[str, Any]:
        processed_arguments_data: Union[List[Dict[str,
                                                  Any]], Dict[str, Any], None] = None
        prompt_args = prompt.arguments

        if isinstance(prompt_args, list):
            temp_list = []
            for item in prompt_args:
                if hasattr(item, 'model_dump'):
                    temp_list.append(item.model_dump(mode='json'))
                elif isinstance(item, dict):
                    temp_list.append(item)
                else:
                    temp_list.append(
                        {"unprocessed_prompt_argument": str(item)})
            processed_arguments_data = temp_list
        elif prompt_args is not None and hasattr(prompt_args, 'model_dump'):
            processed_arguments_data = prompt_args.model_dump(mode='json')
        elif isinstance(prompt_args, dict):
            processed_arguments_data = prompt_args

        return {
            "name": prompt.name,
            "description": prompt.description,
            "arguments": processed_arguments_data,
        }

    async def get_details_of_all_servers(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {}
        try:
            tasks = [self.get_server_capabilities(
                url) for url in self.server_base_urls]
            task_results = await asyncio.gather(*tasks, return_exceptions=False)
            for result in task_results:
                if isinstance(result, dict):
                    server_name = result[MCPClient.MCPServerCapabilities.SERVER_DETAIL.value][
                        MCPClient.MCPServerDetail.NAME.value]
                    if not server_name or not isinstance(server_name, str) or server_name.strip() == "":
                        raise ValueError(
                            "Server name is missing or blank, each server must have a fully and unique name.")
                    if server_name in results:
                        raise ValueError(
                            f"Duplicate server name found: {server_name}. Each server must have a unique name.")
                    results[server_name] = result
                else:
                    raise TypeError(
                        f"Unexpected result type: {type(result)}. Expected {type({})}.")
        except Exception as e:
            msg: str = f"An error occurred while fetching server details. [{e}]"
            self.log.error(msg=msg)
            results = {"error": msg}
        return results

    def get_mcp_server_list(self) -> Dict[int, str]:
        return {i: url for i, url in enumerate(self.server_base_urls)}
