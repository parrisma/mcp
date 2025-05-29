import asyncio
import logging
from typing import List, Dict, Any, Optional, Protocol
from .mcp_client import MCPClient


class MCPInvoke:
    """
    Handles parsing of MCP responses and invoking actions on MCP servers.
    """
    class MCPCapabilityHandler(Protocol):
        async def __call__(self, server_name: str, capability_name: str,
                           parameters: Dict) -> Dict[str, Any]: ...

    def __init__(self,
                 mcp_clients: List[MCPClient],
                 logger: Optional[logging.Logger] = None):
        """
        Initializes the MCPInvoke class.

        :param mcp_client: An instance of MCPClient to interact with MCP servers.
        :param logger: Optional logger instance.
        """
        if len(mcp_clients) == 0:
            raise ValueError("At least one MCPClient must be provided.")

        self._mcp_clients: List[MCPClient] = []
        for mcp_client in mcp_clients:
            if not isinstance(mcp_client, MCPClient):
                raise ValueError("mcp_client must be an instance of MCPClient")
            self._mcp_clients.append(mcp_client)

        self._log: logging.Logger = logger if logger else logging.getLogger(
            __name__)
        if not self._log.hasHandlers():
            logging.basicConfig(
                level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        self._capability_handlers: Dict[str, MCPInvoke.MCPCapabilityHandler] = {
            str(MCPClient.MCPServerCapabilities.TOOLS): self._handle_tool_call,
            str(MCPClient.MCPServerCapabilities.RESOURCES): self._handle_resource_call,
            str(MCPClient.MCPServerCapabilities.RESOURCE_TEMPLATES): self._handle_resource_template_call,
            str(MCPClient.MCPServerCapabilities.PROMPTS): self._handle_prompt_call
        }

    async def _handle_unsupported_call(self,
                                       server_name: str,
                                       capability_name: str,
                                       parameters: Dict[str, Any]) -> Dict[str, Any]:
        raise RuntimeError(
            f"Unsupported MCP capability: {capability_name} for server: {server_name}. ")

    async def _handle_resource_call(self,
                                    server_name: str,
                                    capability_name: str,
                                    parameters: Dict[str, Any]) -> Dict[str, Any]:
        raise (NotImplementedError("Resource handling is not implemented yet."))

    async def _handle_resource_template_call(self,
                                             server_name: str,
                                             capability_name: str,
                                             parameters: Dict[str, Any]) -> Dict[str, Any]:
        raise (NotImplementedError(
            "Resource template handling is not implemented yet."))

    async def _handle_prompt_call(self,
                                  server_name: str,
                                  capability_name: str,
                                  parameters: Dict[str, Any]) -> Dict[str, Any]:
        raise (NotImplementedError("Prompt handling is not implemented yet."))

    async def _handle_tool_call(self,
                                server_name: str,
                                capability_name: str,
                                parameters: Dict[str, Any]) -> Dict[str, Any]:
        self._log.debug(
            f"Handling tool call for server [{server_name}], capability [{capability_name}]")
        result: Dict[str, Any] = {}
        try:
            try:
                for mcp_client in self._mcp_clients:
                    result = await mcp_client.execute_tool(
                        server_name=server_name,
                        tool_name=capability_name,
                        arguments=parameters)
                    if result:  # Take result from first client with a server that can respond
                        break
            except Exception as ex:
                result = {
                    "error": f"Failed to execute tool '{capability_name}' on server '{server_name}': {str(ex)}"}
        except Exception as e:
            result = {
                "error": f"Unexpected error while handling tool call: {str(e)}"}

        return result

    async def _get_mcp_server_responses(self,
                                        mcp_server_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        try:
            if not isinstance(mcp_server_calls, list):
                msg = "Invalid input: 'mcp_server_calls' must be a list."
                self._log.error(msg)
                raise ValueError(msg)
            if len(mcp_server_calls) == 0:
                msg = "No MCP server calls to process."
                self._log.info(msg)
                raise ValueError(msg)

            for call in mcp_server_calls:
                if not isinstance(call, dict):
                    msg = "Each MCP server call must be a dictionary."
                    self._log.error(msg)
                    raise ValueError(msg)

                server_name = call.get("mcp_server_name")
                if not server_name:
                    msg = "MCP server name is required in the call."
                    self._log.error(msg)
                    raise ValueError(msg)

                capability = call.get("mcp_capability")
                if not capability:
                    msg = "MCP capability (e.g. Tool, Prompt etc) is required in the call."
                    self._log.error(msg)
                    raise ValueError(msg)

                capability_name = call.get("mcp_capability_name")
                if not capability_name:
                    msg = "MCP capability (e.g. tool name) is required in the call."
                    self._log.error(msg)
                    raise ValueError(msg)

                parameters = call.get("parameters", {})
                if not isinstance(parameters, dict):
                    msg = "Parameters must be a dictionary."
                    self._log.error(msg)
                    raise ValueError(msg)

                handler: MCPInvoke.MCPCapabilityHandler = self._capability_handlers.get(
                    capability, self._handle_unsupported_call)

                results.append(
                    await handler(server_name, capability_name, parameters))
        except Exception as e:
            msg = f"Error processing MCP server calls: {e}"
            self._log.error(msg)
            results.append({"error": msg})
        return results

    async def process_mcp_responses(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses a list of JSON LLM responses and invokes the appropriate MCP actions if any MCP actions are specified.
        """
        results: Dict[str, Any] = {}
        mcp_server_responses: List[Dict[str, Any]] = []
        clarification_responses: Dict[str, Any] = {}
        try:
            if not isinstance(response, Dict):
                msg = "Invalid input: 'response' must be a dictionary."
                self._log.error(msg)
                raise ValueError(msg)

            response_status = response.get("status", "error")
            if response_status != "success":
                msg = f"Response status is not success: {response_status}"
                self._log.error(msg=msg)
                raise ValueError(msg)

            if "response" in response:
                response_data = response["response"]
                if not isinstance(response_data, Dict):
                    msg = "Response data must be a dictionary."
                    self._log.error(msg)
                    raise ValueError(msg)

                mcp_server_calls = response_data.get("mcp_server_calls", {})
                if len(mcp_server_calls) == 0:
                    self._log.info(
                        "No MCP server calls found in the response.")
                if not isinstance(mcp_server_calls, list):
                    msg = "MCP server calls must be a list."
                    self._log.error(msg)
                    raise ValueError(msg)
                else:
                    mcp_server_responses = await self._get_mcp_server_responses(
                        mcp_server_calls)

                clarifications = response_data.get("clarifications", {})
                if len(clarifications) == 0:
                    self._log.info("No clarifications found in the response.")
            else:
                msg = "Response does not contain 'response' key."
                self._log.error(msg)
                raise ValueError(msg)
        except Exception as e:
            self._log.exception(
                f"Unexpected error processing response item {response}: {e}")

        results["mcp_server_responses"] = mcp_server_responses
        results["clarification_responses"] = clarification_responses
        return results

# Example Usage (requires an MCPClient instance and an event loop)


async def test():

    mcp_client = MCPClient(
        [f"http://localhost:6277"],)
    invoker = MCPInvoke(mcp_clients=[mcp_client])

    test_responses = [
        {
            "response": {
                "answer": {},
                "clarifications": [],
                "mcp_server_calls": [
                    {
                        "id": "1",
                        "mcp_capability": "tools",
                        "mcp_server_name": "Demo",
                        "mcp_capability_name": "add",
                        "parameters": {"a": 9, "b": 5}
                    }
                ],
                "thinking": {
                    "next_steps": "After receiving the result of the addition, I will proceed with the multiplication.",
                    "reasoning": "The goal is to compute (9+5)*3. The first step is to add 9 and 5 using the add tool from the MCP server."
                }
            },
            "status": "success"
        }
    ]

    for test_response in test_responses:
        results = await invoker.process_mcp_responses(test_response)
        for key, value in results.items():
            print(f"{key}: {value}")

if __name__ == "__main__":
    asyncio.run(test())
