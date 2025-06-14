# pylint: disable=C0301
import asyncio
import logging
import urllib.parse
from calendar import c
from enum import Enum
from math import e
from typing import List, Dict, Any, Optional, Text, Union, Literal, final
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from pydantic import AnyUrl
import pydantic
import mcp.types as types


class MCPClient:
    """
    A client to connect to MCP servers and retrieve their capabilities.
    """
    class FailedToGetMCPServerCapabilities(Exception):
        pass

    class FailedToFindMCPServerURL(Exception):
        pass

    class FailedToEstablishMCPServerSession(Exception):
        pass

    class FailedToInvokeMCPServerCapability(Exception):
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

    class MCPServerTransport(str, Enum):
        SSE = "sse"
        STDIO = "stdio"
        STREAMABLE_HTTP = "streamable-http"

        def __str__(self) -> Literal['sse', 'stdio', 'streamable-http']:
            return self.value

    def __init__(self, server_base_urls: List[str]):
        if not server_base_urls:
            raise ValueError("At least one server base URL must be provided.")
        self._server_base_urls: List[str] = server_base_urls
        self._capabilities_cache: Dict[str, Dict[str, Any]] = {}
        self._transport: MCPClient.MCPServerTransport = MCPClient.MCPServerTransport.SSE
        self._log: logging.Logger = logging.getLogger(
            __name__)  # Added logger instance
        # Configure basic logging if no handlers are already set for the root logger
        # This helps ensure logs are visible if the calling application hasn't configured logging
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler()]
            )

    def get_trasnsport(self) -> "MCPClient.MCPServerTransport":
        return self._transport

    def get_full_server_url(self, server_base_url: str) -> str:
        return f"{server_base_url.rstrip('/')}/{str(self._transport).lower()}"

    async def __aenter__(self) -> "MCPClient":
        self._log.debug("MCPClient entering async context.")
        # Perform any setup if needed, though for this client,
        # connections are typically established per-method call.
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self._log.debug("MCPClient exiting async context.")
        # Perform any cleanup if needed.
        # If an exception occurred, it will be passed here.
        # Return False (or nothing, which defaults to False) to re-raise the exception.
        # Return True to suppress the exception (generally not recommended unless handled).
        pass

    async def get_server_capabilities(self, server_base_url: str) -> Dict[str, Any]:

        sse_url: str = self.get_full_server_url(server_base_url)

        if server_base_url in self._capabilities_cache:
            self._log.info(
                f"Returning cached capabilities for [{server_base_url}]")
            return self._capabilities_cache[server_base_url]

        capabilities: Dict[str, Any] = {}
        capabilities[MCPClient.MCPServerCapabilities.SERVER_DETAIL.value] = {}
        capabilities[MCPClient.MCPServerCapabilities.TOOLS.value] = []
        capabilities[MCPClient.MCPServerCapabilities.RESOURCES.value] = []
        capabilities[MCPClient.MCPServerCapabilities.RESOURCE_TEMPLATES.value] = []
        capabilities[MCPClient.MCPServerCapabilities.PROMPTS.value] = []

        try:
            self._log.info(
                f"Attempting to connect to MCP server at: {sse_url}")
            async with sse_client(sse_url) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    initialize_result: types.InitializeResult = await session.initialize()
                    await asyncio.sleep(1)

                    self._log.info(
                        f"Successfully connected to {sse_url}. Fetching capabilities from {initialize_result.serverInfo.name}")

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

            self._capabilities_cache[server_base_url] = capabilities
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
                url) for url in self._server_base_urls]
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
            self._log.error(msg=msg)
            results = {"error": msg}
        return results

    async def _get_server_url(self, server_name: str) -> Optional[str]:
        """
        Retrieves the base URL for a given server name from the cache.
        If the cache is empty, it attempts to populate it first.

        :param server_name: The unique name of the MCP server.
        :return: The base URL of the server, or None if not found.
        """
        try:
            if not self._capabilities_cache:
                self._log.info(
                    "_get_server_url: Capabilities cache is empty, populating...")
                await self.get_details_of_all_servers()  # This populates the cache by base_url

            # Iterate through the cached capabilities (which are keyed by base_url)
            # to find the server by its name.
            found_url: Optional[str] = None
            for base_url, cached_data in self._capabilities_cache.items():
                if isinstance(cached_data, dict):
                    server_detail = cached_data.get(
                        self.MCPServerCapabilities.SERVER_DETAIL.value)
                    if isinstance(server_detail, dict):
                        if server_detail.get(self.MCPServerDetail.NAME.value, None) == server_name:
                            found_url = server_detail.get(
                                self.MCPServerDetail.SERVER_URL.value, None)
                        if found_url:
                            # Validate found_url is a valid URL
                            try:
                                pydantic.AnyUrl(found_url)
                                self._log.debug(
                                    f"Found valid URL '{found_url}' for server name '{server_name}'.")
                            except pydantic.ValidationError:
                                msg = f"Found URL '{found_url}' for server name '{server_name}', but it is not a valid URL."
                                self._log.error(msg=msg)
                                found_url = None
                                raise ValueError(msg) from None
                            break
                else:
                    raise TypeError(
                        f"Internal error, Expected cached server data to be a dict, got {type(cached_data)} for base_url {base_url}.")
            if not found_url:
                msg = f"_get_server_url: Server name '{server_name}' not found in the cache."
                self._log.error(msg=msg)
                raise MCPClient.FailedToFindMCPServerURL(msg)
            return found_url
        except Exception as e:
            msg = f"_get_server_url: An error occurred while retrieving the server URL for '{server_name}': {e}"
            self._log.error(msg=msg)
            raise MCPClient.FailedToFindMCPServerURL(msg) from e

    async def _get_server_session(self, server_name: str) -> Optional[ClientSession]:
        session: Optional[ClientSession] = None
        try:
            sse_url: Optional[str] = await self._get_server_url(server_name)
            if sse_url:
                sse_url = self.get_full_server_url(sse_url)
                async with sse_client(sse_url) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        initialize_result: types.InitializeResult = await session.initialize()
                        await asyncio.sleep(1)
                        self._log.info(
                            f"Successfully connected to {sse_url}. created new session with {initialize_result.serverInfo.name}")

        except Exception as e:
            msg = f"_get_server_session: An error occurred while getting session for server '{server_name}': {e}"
            self._log.error(msg=msg)
            raise MCPClient.FailedToEstablishMCPServerSession(msg) from e
        return session

    def _extract_tool_result(self, tool_result: types.CallToolResult) -> List[str]:
        result: List[str] = []
        if tool_result is None:
            result = ["Error, No result retruned from tool execution."]
        if tool_result.isError:
            result = ["Error, Tool reported an error and did not return a result"]
        res: List[str] = []
        for content in tool_result.content:
            if isinstance(content, types.TextContent):
                res.append(str(content.text))
            else:
                result = [
                    f"Error, Unsupported tool result type: [{type(content)}]"]
        if len(res) > 0:
            result = res

        return result

    def _extract_resource_result(self,
                                 resource_result: types.ReadResourceResult) -> List[str]:
        result: List[str] = []
        if resource_result is None:
            result = ["Error, No result retruned from tool execution."]
        res: List[str] = []
        for content in resource_result.contents:
            if isinstance(content, types.TextResourceContents):
                res.append(str(content.text))
            else:
                result = [
                    f"Error, Unsupported tool result type: [{type(content)}]"]
        if len(res) > 0:
            result = res

        return result

    def _request_source(self,
                        server_name: str,
                        capability_name: str,
                        arguments: dict[str, Any]) -> Optional[str]:
        params_flat = ", ".join(f"{k}={v!r}" for k, v in arguments.items())
        return f"Capability [{capability_name}] called on server [{server_name}] with parameters: [{params_flat}]"

    def _encode_arguments_into_url(self,
                                   url: str,
                                   arguments: dict[str, Any]) -> pydantic.AnyUrl:
        try:
            params: str = ""
            if len(arguments) > 0:
                if len(arguments) == 1:
                    params = f"{urllib.parse.quote(str(next(iter(arguments.values()))))}"
                else:
                    for key, value in arguments.items():
                        if len(params) > 0:
                            params = f"{params}/"
                        params = f"{key}/{urllib.parse.quote(value)}"
            return pydantic.AnyUrl(f"{url.split("//")[0] + "//"}{params}")
        except Exception as e:
            msg = f"_encode_arguments_into_url: An error occurred while encoding arguments into URL '{url}': {e}"
            self._log.error(msg=msg)
            raise ValueError(msg) from e

    async def execute_resource(
        self,
        server_name: str,
        resource_name: str,
        resource_uri: str,
        arguments: dict[str, Any]
    ) -> Any:
        session: Optional[ClientSession] = None
        result: Optional[Dict[str, Any]] = {}
        result["source"] = self._request_source(
            server_name=server_name,
            capability_name=resource_name,
            arguments=arguments)
        try:
            sse_url: Optional[str] = await self._get_server_url(server_name)
            if sse_url:
                sse_url = self.get_full_server_url(sse_url)
                async with sse_client(sse_url) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        initialize_result: types.InitializeResult = await session.initialize()
                        self._log.info(
                            f"Successfully connected to {sse_url} to get resource '{resource_name}' on server '{initialize_result.serverInfo.name}'.")
                        resource_any_uri: pydantic.AnyUrl = self._encode_arguments_into_url(
                            url=resource_uri, arguments=arguments)
                        resource_result: types.ReadResourceResult = await session.read_resource(resource_any_uri)
                        if resource_result is None:
                            raise MCPClient.FailedToInvokeMCPServerCapability(
                                f"Resource '{resource_name}' returned no result from server '{server_name}'.")
                        result["results"] = self._extract_resource_result(
                            resource_result)
            else:
                raise MCPClient.FailedToFindMCPServerURL(
                    f"Server URL for '{server_name}' could not be found in the cache.")
        except Exception as e:
            msg = f"execute_resource: An error occurred while executing tool '{resource_name}' on server '{server_name}': {e}"
            self._log.error(msg=msg)
            result = {
                "error": msg,
                "details": str(e)
            }
        return result

    async def execute_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any]
    ) -> Any:
        session: Optional[ClientSession] = None
        result: Optional[Dict[str, Any]] = {}
        result["source"] = self._request_source(
            server_name=server_name,
            capability_name=tool_name,
            arguments=arguments)
        try:
            sse_url: Optional[str] = await self._get_server_url(server_name)
            if sse_url:
                sse_url = self.get_full_server_url(sse_url)
                async with sse_client(sse_url) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        initialize_result: types.InitializeResult = await session.initialize()
                        self._log.info(
                            f"Successfully connected to {sse_url} to execute tool '{tool_name}' on server '{initialize_result.serverInfo.name}'.")
                        tool_result: types.CallToolResult = await session.call_tool(tool_name, arguments)
                        if tool_result is None:
                            raise MCPClient.FailedToInvokeMCPServerCapability(
                                f"Tool '{tool_name}' returned no result from server '{server_name}'.")
                        result["results"] = self._extract_tool_result(
                            tool_result)
            else:
                raise MCPClient.FailedToFindMCPServerURL(
                    f"Server URL for '{server_name}' could not be found in the cache.")
        except Exception as e:
            msg = f"execute_tool: An error occurred while executing tool '{tool_name}' on server '{server_name}': {e}"
            self._log.error(msg=msg)
            result = {
                "error": msg,
                "details": str(e)
            }
        return result

    def get_mcp_server_url_list(self) -> Dict[int, str]:
        return {i: url for i, url in enumerate(self._server_base_urls)}
