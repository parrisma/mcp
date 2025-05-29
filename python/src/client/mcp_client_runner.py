import asyncio
import argparse
import json
import logging
import datetime
import os

from pathlib import Path
from typing import List, Dict, Any, Tuple
import mcp
from yarl import URL

from .mcp_client import MCPClient
from ..server.network_utils import NetworkUtils
from .ollama_utils import ollama_running_and_model_loaded, ollama_host, ollama_model, get_llm_response
from .mcp_client_web_server import MCPClientWebServer
from .mcp_invoke import MCPInvoke


# Custom Exception for LLM call failures
class FailedLLMCall(Exception):
    """Custom exception for when a call to the LLM fails."""
    pass


class MCPClientRunner:
    class ErrorGettingServerCapabilities(Exception):
        pass

    def __init__(self) -> None:
        """
        Initializes the MCPClientRunner.
        Argument parsing and connection setup are handled here.
        """
        self._log: logging.Logger = self._configure_logging()

        args: argparse.Namespace = self._parse_command_line()

        self._debug_mode: bool = False  # Initialize debug_mode
        self._set_logging(args)

        self._ollama_host_url: URL
        self._ollama_model_name: str
        self._ollama_host_url, self._ollama_model_name = self._get_ollama_url_and_model(
            args)

        self._mcp_host_urls: List[str] = self._get_mcp_host_urls(args)
        self._mcp_client: MCPClient = MCPClient(
            server_base_urls=self._mcp_host_urls)

        self._invoker: MCPInvoke = MCPInvoke([self._mcp_client])

        self._web_server_host: str
        self._web_server_port: int
        self._web_server_host, self._web_server_port = self._get_validated_web_server_address(
            args)
        self._web_server = MCPClientWebServer(host=self._web_server_host,
                                              port=self._web_server_port)

    def _parse_command_line(self) -> argparse.Namespace:
        """
        Parses command-line arguments or uses environment variables/defaults
        to configure server connections.
        Returns a list of validated server URLs.
        """
        parser = argparse.ArgumentParser(description="MCP Client Runner")
        parser.add_argument(
            "--host",
            type=str,
            default=os.environ.get("MCP_CLIENT_HOST"),
            help="Hostname or IP address of the MCP server. "
                 "Overrides MCP_CLIENT_HOST env var. "
                 "Used if --host-list is not provided."
        )
        parser.add_argument(
            "--port",
            type=int,
            default=os.environ.get("MCP_CLIENT_PORT"),
            help="Port number of the MCP server. "
                 "Overrides MCP_CLIENT_PORT env var. "
                 "Used if --host-list is not provided."
        )
        parser.add_argument(
            "--host-list",
            type=Path,
            default=os.environ.get("MCP_CLIENT_HOST_LIST_FILE"),
            help="Path to a JSON file containing a list of server connections. "
                 "Each item should be an object with 'host' and 'port' keys. "
                 "Overrides MCP_CLIENT_HOST_LIST_FILE env var. "
                 "If provided, --host and --port arguments are ignored."
        )
        parser.add_argument(
            "--ollama-host-url",
            type=str,
            default=os.environ.get("MCP_OLLAMA_HOST_URL"),
            help="URL of the Ollama server. Overrides MCP_OLLAMA_HOST_URL env var."
        )
        parser.add_argument(
            "--ollama-model-name",
            type=str,
            default=os.environ.get("MCP_OLLAMA_MODEL_NAME"),
            help="Name of the Ollama model to use. Overrides MCP_OLLAMA_MODEL_NAME env var."
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            default=os.environ.get(
                "MCP_CLIENT_DEBUG", "false").lower() == "true",
            help="Enable debug logging. Overrides MCP_CLIENT_DEBUG env var."
        )
        parser.add_argument(
            "--web-host",
            type=str,
            default=os.environ.get("MCP_CLIENT_WEB_HOST", "0.0.0.0"),
            help="Hostname for the client's web server. Overrides MCP_CLIENT_WEB_HOST env var."
        )
        parser.add_argument(
            "--web-port",
            type=int,
            default=os.environ.get("MCP_CLIENT_WEB_PORT", "9312"),
            help="Port for the client's web server. Overrides MCP_CLIENT_WEB_PORT env var."
        )
        args: argparse.Namespace = parser.parse_args()
        return args

    def _configure_logging(self) -> logging.Logger:
        log: logging.Logger = logging.getLogger("mcp-client-runner")
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler()]
            )
        return log

    def _set_logging(self, args: argparse.Namespace) -> None:
        """Sets debug mode and configures logging levels based on args."""
        self._debug_mode = args.debug
        if self._debug_mode:
            self._log.setLevel(logging.DEBUG)
            logging.getLogger('mcp_client').setLevel(
                logging.DEBUG)  # Also set for mcp_client
            self._log.debug("Debug mode enabled for client runner.")

    def _get_ollama_url_and_model(self, args: argparse.Namespace) -> Tuple[URL, str]:
        """Sets Ollama host URL and model name from args and logs them."""
        ollama_host_url: URL = URL()
        if args.ollama_host_url:
            ollama_host_url = URL(args.ollama_host_url)
            self._log.info(f"Ollama host URL set to: {ollama_host_url}")
        ollama_model_name: str = ""
        if args.ollama_model_name:
            ollama_model_name = args.ollama_model_name
            self._log.info(
                f"Ollama model name set to: {ollama_model_name}")
        return (ollama_host_url, ollama_model_name)

    def _get_mcp_host_urls(self, args: argparse.Namespace) -> List[str]:
        host_urls: List[str] = []
        connections_to_process: List[Tuple[str, int]] = []

        if args.host_list:
            config_file_path = Path(args.host_list)
            if config_file_path.is_file():
                self._log.info(
                    f"Loading server connections from host list file: {config_file_path}")
                try:
                    with open(config_file_path, "r", encoding="utf-8") as f:
                        servers_config = json.load(f)
                    if not isinstance(servers_config, list):
                        raise ValueError(
                            "JSON file content must be a list of server objects.")
                    for server_item in servers_config:
                        if not isinstance(server_item, dict) or \
                           "host" not in server_item or \
                           "port" not in server_item:
                            self._log.warning(
                                f"Skipping invalid server entry in file: {server_item}. "
                                "Each entry must be an object with 'host' and 'port'."
                            )
                            continue
                        try:
                            port = int(server_item["port"])
                            connections_to_process.append(
                                (str(server_item["host"]), port))
                        except ValueError:
                            self._log.warning(
                                f"Skipping server entry with invalid port: {server_item}")
                except json.JSONDecodeError:
                    msg: str = f"Error decoding JSON from file: {config_file_path}"
                    self._log.error(msg)
                    raise ValueError(msg)
                except Exception as e:
                    msg: str = f"Error reading or processing config file {config_file_path}: {e}"
                    self._log.error(msg)
                    raise ValueError(msg) from e
            else:
                self._log.warning(
                    f"Specified configuration file not found: {config_file_path}. "
                    "Falling back to --host/--port or defaults."
                )

        if not connections_to_process:  # If host list file wasn't used or was empty/invalid
            host_to_use: str = args.host
            port_to_use_str = args.port

            if not host_to_use:  # Not from arg, try env or hardcoded default
                host_to_use = os.environ.get("MCP_CLIENT_HOST", "127.0.0.1")
            if not port_to_use_str:  # Not from arg, try env or hardcoded default
                port_to_use_str = os.environ.get("MCP_CLIENT_PORT", "6277")

            if host_to_use and port_to_use_str:
                try:
                    port_val = int(port_to_use_str)
                    connections_to_process.append((host_to_use, port_val))
                except ValueError as ve:
                    msg: str = f"Invalid port value '{port_to_use_str}' for single server connection."
                    self._log.error(msg)
                    raise ValueError(msg) from ve
            else:  # Should not happen if defaults are set, but as a fallback
                self._log.error(
                    "No server host or port configured via arguments, host list file, or environment variables.")

        for host, port in connections_to_process:
            if not NetworkUtils.is_resolvable_hostname(host):  # Corrected call
                self._log.error(
                    f"Hostname '{host}' is not resolvable. Skipping this connection."
                )
                continue

            if not (0 < port < 65536):
                self._log.error(
                    f"Port {port} for host '{host}' is invalid. Skipping this connection."
                )
                continue

            host_url: str = f"http://{host}:{port}"
            host_urls.append(host_url)
            self._log.info(f"Configured client connection URL: {host_url}")

        if not host_urls:
            msg = "No valid server connections were configured. Client will not connect to any servers."
            self._log.warning(msg)
            raise ValueError(msg)

        return host_urls

    def _get_validated_web_server_address(self, args: argparse.Namespace) -> Tuple[str, int]:
        web_host: str = args.web_host
        web_port: int = args.web_port

        if not NetworkUtils.is_resolvable_hostname(web_host):
            msg: str = f"Web server hostname '{web_host}' is not resolvable."
            self._log.error(msg)
            raise ValueError(msg)

        if not (0 < web_port < 65536):
            msg = f"Web server port {web_port} for host '{web_host}' is invalid. Must be between 1 and 65535."
            self._log.error(msg)
            raise ValueError(msg)

        if not NetworkUtils.is_free_port(web_host, web_port):
            msg = f"Web server port {web_port} on host '{web_host}' is not available."
            self._log.error(msg)
            raise ValueError(msg)

        self._log.info(
            f"Validated web server address: http://{web_host}:{web_port}")
        return web_host, web_port

    def _ensure_ollama_ready(self) -> None:
        if (not ollama_running_and_model_loaded(host_url=self._ollama_host_url,
                                                model_name=self._ollama_model_name)):
            msg: str = f"Ollama server at {self._ollama_host_url} is not running or model '{self._ollama_model_name}' is not loaded."
            self._log.error(msg)
            raise ValueError(msg)
        self._log.info(
            f"Ollama server at {self._ollama_host_url} is running and model '{self._ollama_model_name}' is loaded.")

    def _current_time_as_dict(self) -> Dict[str, Any]:
        now = datetime.datetime.now(datetime.timezone.utc).astimezone()
        return {
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
            "timezone": now.tzname()
        }

    def ping_callback(self,
                      params: Dict) -> Dict:
        path: str = params.get(
            MCPClientWebServer.QueryParamKeys.PATH.value, "")
        args: Dict[str, Any] = params.get(
            MCPClientWebServer.QueryParamKeys.ARGS.value, {})

        return {
            "ping": self._current_time_as_dict(),
            "path": path,
            "args": args,
            "message": "ok"
        }

    def _get_config(self) -> Dict[str, Any]:
        return {
            "ollama_host_url": str(self._ollama_host_url) if self._ollama_host_url else None,
            "ollama_model_name": self._ollama_model_name,
            "mcp_host_urls": self._mcp_host_urls,
            "time": self._current_time_as_dict()
        }

    def get_config(self,
                   params: Dict) -> Dict:
        return self._get_config()

    async def _get_mcp_responses_and_clarifications(self,
                                                    questions: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, str]]:
        mcp_responses: Dict[str, Any] = {}
        clarifications: Dict[str, Any] = {}

        if not questions:
            raise ValueError("Questions parameter cannot be empty.")
        if not isinstance(questions, dict):
            raise ValueError("Questions parameter must be a dictionary.")
        try:
            mcp_res = await self._invoker.process_mcp_responses(response=questions)
            mcp_responses = mcp_res.get("mcp_server_responses", {})
            clarifications = mcp_res.get("clarification_responses", {})
        except Exception as e:
            msg: str = f"Error processing MCP responses and clarifications: {e}"
            self._log.error(msg)

        return mcp_responses, clarifications

    async def _get_model_response(self,
                                  params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            capabilities: Dict[str, Any] = await self._get_capabilities()
            if "error" in capabilities:  # Propagate error from _get_capabilities
                raise MCPClientRunner.ErrorGettingServerCapabilities(
                    capabilities["error"])

            goal: str = params['args'].get("goal", "")
            if not goal:
                msg = "User prompt (goal) is required but was empty."
                self._log.error(msg)
                # No need to raise ValueError here, just return an error dict
                return {"error": msg, "type": "ValueError"}

            # Check to see if there are un answer MCP Model calls or User clarification questions
            # If so, we will get answewrs to MCP calls pass them to the LLM via the prompt.
            questions: Dict[str, Any] = params['args'].get("questions", {})
            mcp_responses: Dict[str, Any] = {}
            clarifications: Dict[str, Any] = {}
            if questions:
                if isinstance(questions, str):
                    try:
                        questions = json.loads(questions)
                    except json.JSONDecodeError as e:
                        msg = f"Failed to decode questions, expecting valid JSON: {e}"
                        self._log.error(msg)
                        raise ValueError(msg)
                mcp_responses, clarifications = await self._get_mcp_responses_and_clarifications(
                    questions=questions
                )

            llm_call_successful, llm_content = get_llm_response(
                user_goal=goal,
                mcp_server_descriptions=json.dumps(capabilities),
                mcp_responses=mcp_responses,
                clarifications=clarifications,
                model=self._ollama_model_name,
                host=str(self._ollama_host_url),
                temperature=0.7
            )

            if not llm_call_successful:
                error_message = str(
                    llm_content) if llm_content else "Unknown LLM error during get_initial_response"
                raise FailedLLMCall(error_message)

            # Assuming llm_content is the actual response data from the model on success
            return {"response": llm_content, "status": "success"}

        except FailedLLMCall as flc:
            msg = f"LLM call failed: {flc}"
            self._log.error(msg)
            return {"error": msg, "type": "FailedLLMCall"}
        except ValueError as ve:  # This will now catch ValueErrors raised explicitly if any
            msg = f"Input error for model response: {ve}"
            self._log.error(msg)
            return {"error": msg, "type": "ValueError"}
        except Exception as e:
            msg = f"An unexpected error occurred while getting model response: {e}"
            self._log.exception(msg)
            return {"error": "An internal server error occurred.", "type": "Exception"}

    def get_model_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper for the async get_model_response method."""
        return asyncio.run(self._get_model_response(params))

    async def _get_capabilities(self) -> Dict[str, Any]:
        """
        Retrieves the capabilities of the MCP server.
        Returns a dictionary with server capabilities.
        """
        try:
            return await self._mcp_client.get_details_of_all_servers()
        except Exception as e:
            msg: str = f"Failed to get MCP server capabilities: {e}"
            self._log.error(msg=msg)
            return {"error": msg}

    def get_capabilities(self,
                         params: Dict) -> Dict:
        return asyncio.run(self._get_capabilities())

    async def _start_services(self) -> None:
        """
        Ensures Ollama is ready, sets up web server routes, and starts the web server.
        """
        self._ensure_ollama_ready()
        self._web_server.add_route('/config', self.get_config)
        self._web_server.add_route('/capability', self.get_capabilities)
        self._web_server.add_route('/ping', self.ping_callback)
        self._web_server.add_route('/model_response', self.get_model_response)
        self._web_server.run()

    async def run(self) -> None:
        await self._start_services()


async def main() -> None:
    runner = MCPClientRunner()
    await runner.run()

if __name__ == "__main__":
    asyncio.run(main())
