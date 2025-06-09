import asyncio
import argparse
import json
import logging
import datetime
import os
import uuid

from pathlib import Path
from tkinter import N
from tkinter.filedialog import Open
from typing import List, Dict, Any, Optional, Tuple
from click import prompt
from yarl import URL

from .mcp_client import MCPClient
from ..server.network_utils import NetworkUtils
from .ollama_utils import Ollama
from .mcp_client_web_server import MCPClientWebServer
from .mcp_invoke import MCPInvoke
from .openrouter_utils import OpenRouter
from .prompts import Prompts


class MCPClientRunner:

    class ErrorGettingServerCapabilities(Exception):
        pass

    class FailedLLMCall(Exception):
        pass

    class ErrorStartingClientRunner(Exception):
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

        self._ollama_host_url: URL | None = None
        self._ollama_model_name: str | None = None
        self._ollama_enabled: bool = args.ollama_enabled
        if self._ollama_enabled:
            self._ollama_host_url, self._ollama_model_name = self._get_ollama_url_and_model(
                args)
            self._ollama: Ollama = Ollama()
        else:
            self._log.info(
                "Ollama integration is disabled, no Ollama conenction will be made.")

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
        self._add_web_routes()

        self._mcp_responses_cache: Dict[uuid.UUID, Dict[str, Any]] = {}
        self._clarifications_cache: Dict[uuid.UUID, Dict[str, str]] = {}

        self._openrouter_url: URL = URL(args.openrouter_url)
        self._openrouter_model: str = args.openrouter_model
        self._openrouter_api_key: str = args.openrouter_api_key
        self._openrouter: OpenRouter | None = self._setup_openrouter(openrouter_url=self._openrouter_url,
                                                                     openrouter_model=self._openrouter_model,
                                                                     openrouter_api_key=self._openrouter_api_key)
        self._prompts: Prompts = Prompts()

    def _setup_openrouter(self,
                          openrouter_url: URL,
                          openrouter_model: str,
                          openrouter_api_key: str) -> Optional[OpenRouter]:
        if not openrouter_url or not openrouter_model or not openrouter_api_key:
            self._log.warning(
                "OpenRouter is not enabled: need all of URL, model & API key to be fully defined, "
                f"got URL: {openrouter_url}, model: {openrouter_model}, API key: {'set' if openrouter_api_key else 'not set'}."
            )
        else:
            self._log.info(f"Openrouter avaialble")
            return OpenRouter(openrouter_url=openrouter_url.name,
                              model_name=openrouter_model,
                              api_key=openrouter_api_key,)
        return None

    def _add_web_routes(self) -> None:
        self._web_server.add_route(
            route='/config', methods=['GET'], handler=self.get_config)
        self._web_server.add_route(
            route='/capability', methods=['GET'], handler=self.get_capabilities)
        self._web_server.add_route(
            route='/ping', methods=['GET'], handler=self.ping_callback)
        self._web_server.add_route(
            route='/model_response', methods=['GET', 'POST'], handler=self.get_model_response)

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
            "--ollama-enabled",
            action="store_true",
            default=os.environ.get("MCP_OLLAMA_ENABLED",
                                   "false").lower() == "true",
            help="Enable Ollama integration. Overrides MCP_OLLAMA_ENABLED env var. Defaults to false."
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
        parser.add_argument(
            "--openrouter-url",
            type=str,
            default=os.environ.get(
                "OPENROUTER_URL", "https://openrouter.ai/api/v1"),
            help="URL of the OpenRouter server. Overrides OPENROUTER_URL env var. Defaults to https://openrouter.ai/api/v1"
        )
        parser.add_argument(
            "--openrouter-model",
            type=str,
            default=os.environ.get(
                "OPENROUTER_MODEL", "google/gemini-2.5-pro-preview"),
            help="Model name for OpenRouter. Overrides OPENROUTER_MODEL env var. Defaults to 'google/gemini-2.5-pro-preview'."
        )
        parser.add_argument(
            "--openrouter-api-key",
            type=str,
            default=os.environ.get("OPENROUTER_API_KEY", ""),
            help="API key for OpenRouter. Overrides OPENROUTER_API_KEY env var. Defaults to empty string."
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
        if not self._ollama_enabled:
            self._log.info(
                "Ollama integration is disabled, skipping readiness check.")
        else:
            if self._ollama_host_url is None or self._ollama_model_name is None:
                msg: str = "Ollama host URL or model name is not set."
                self._log.error(msg)
                raise ValueError(msg)
            if (not self._ollama.ollama_running_and_model_loaded(host_url=self._ollama_host_url,
                                                                 model_name=self._ollama_model_name)):
                msg: str = f"Ollama server at {self._ollama_host_url} is not running or model '{self._ollama_model_name}' is not loaded."
                self._log.error(msg)
                raise ValueError(msg)
            self._log.info(
                f"Ollama server at {self._ollama_host_url} is running and model '{self._ollama_model_name}' is loaded.")
        return

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
            "ollama_host_url": str(self._ollama_host_url) if self._ollama_host_url else "Not Set",
            "ollama_model_name": self._ollama_model_name if self._ollama_host_url else "Not Set",
            "ollama_enabled": self._ollama_enabled,
            "mcp_host_urls": self._mcp_host_urls,
            "openrouter_url": str(self._openrouter_url) if self._openrouter_url else "Not Set",
            "openrouter_model": self._openrouter_model if self._openrouter_model else "Not Set",
            "openrouter_api_key": self._openrouter_api_key if self._openrouter_api_key else "Not Set",
            "time": self._current_time_as_dict()
        }

    def get_config(self,
                   params: Dict) -> Dict:
        return self._get_config()

    def _get_cache_and_merge_mcp_responses_by_session(self,
                                                      mcp_responses: List[Dict[str, Any]],
                                                      llm_session: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Adds mcp_responses to the session cache and returns the merged responses.
        """
        try:
            mcp_sesson_responses: Dict[str, Any] = self._mcp_responses_cache.get(
                llm_session, {})
            for mcp_response in mcp_responses:
                mcp_sesson_responses[mcp_response["source"]] = mcp_response
            self._mcp_responses_cache[llm_session] = mcp_sesson_responses
            return list(mcp_sesson_responses.values())
        except Exception as e:
            msg: str = f"Error merging MCP responses by session: {e}"
            self._log.error(msg)
            return mcp_responses

    def _get_cache_and_merge_clarifications_by_session(self,
                                                       clarifications: List[Dict[str, Any]],
                                                       llm_session: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Adds clarifications to the session cache and returns the merged clarifications.
        """
        try:
            clarifications_session: Dict[str, Any] = self._clarifications_cache.get(
                llm_session, {})
            for clarification in clarifications:
                clarifications_session[clarification["question"]
                                       ] = clarification
            self._clarifications_cache[llm_session] = clarifications_session
            return list(clarifications_session.values())
        except Exception as e:
            msg: str = f"Error merging clarifications by session: {e}"
            self._log.error(msg)
            return clarifications

    async def _get_model_response(self,
                                  params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handles the /model_response endpoint, processing incoming data,
        invoking MCP actions, and calling the LLM.
        """
        try:
            if not params or not isinstance(params, dict):
                msg = "Invalid or empty parameters provided for model response."
                self._log.error(msg)
                raise ValueError(msg)

            args: Dict[str, Any] = params.get("args", {})
            if not args or not isinstance(args, dict):
                msg = "No or invalid 'args' provided in parameters for model response."
                self._log.error(msg)
                raise ValueError(msg)

            llm_session_id: str | None = args.get("session")
            if not llm_session_id:
                msg = "No session ID provided in parameters for model response."
                self._log.error(msg)
                raise ValueError(msg)

            try:
                llm_session = uuid.UUID(llm_session_id)
            except ValueError as e:
                msg = f"Invalid session ID provided: {llm_session_id}. Must be a valid UUID."
                self._log.error(msg)
                raise ValueError(msg) from e

            capabilities: Dict[str, Any] = await self._get_capabilities()
            if "error" in capabilities:  # Propagate error from _get_capabilities
                raise MCPClientRunner.ErrorGettingServerCapabilities(
                    capabilities["error"])

            goal: str = args.get("goal", "")
            if not goal:
                msg = "User prompt (goal) is required but was empty."
                self._log.error(msg)
                raise ValueError(msg)

            # Extract previous LLM response structure and user clarifications
            previous_llm_response_structure: Dict[str, Any] = args.get("response", {})
            user_clarifications: List[Dict[str, Any]] = args.get("clarifications", [])

            # Process MCP server calls from the previous LLM response
            previous_mcp_calls = previous_llm_response_structure.get("mcp_server_calls", [])
            mcp_responses: List[Dict[str, Any]] = await self._invoker.get_mcp_server_responses(previous_mcp_calls)

            # Process user responses to clarifications
            clarification_responses: List[Dict[str, Any]] = await self._invoker.get_clarification_responses(user_clarifications)

            # Cache and merge responses and clarifications
            merged_mcp_responses = self._get_cache_and_merge_mcp_responses_by_session(
                mcp_responses=mcp_responses,
                llm_session=llm_session
            )
            merged_clarifications = self._get_cache_and_merge_clarifications_by_session(
                clarifications=clarification_responses,
                llm_session=llm_session
            )

            full_prompt: Optional[str] = self._prompts.build_prompt(user_goal=goal,
                                                                    session_id=llm_session,
                                                                    mcp_server_descriptions=capabilities,
                                                                    mcp_responses=merged_mcp_responses,
                                                                    clarifications=merged_clarifications)

            llm_call_successful: bool = False
            llm_content: Dict[str, Any] = {}

            if not full_prompt:
                msg = "Failed to generate a valid prompt for the LLM."
                self._log.error(msg)
                raise ValueError(msg)

            if self._openrouter:
                llm_call_successful, llm_content = self._openrouter.get_llm_response(
                    prompt=full_prompt
                )
            elif self._ollama_enabled and self._ollama:
                 llm_call_successful, llm_content = self._ollama.get_llm_response(prompt=full_prompt,
                                                                                 model=str(
                                                                                     self._ollama_model_name),
                                                                                 host=str(
                                                                                     self._ollama_host_url),
                                                                                 temperature=0.3
                                                                                 )
            else:
                msg = "No LLM provider (OpenRouter or Ollama) is enabled or configured."
                self._log.error(msg)
                raise MCPClientRunner.FailedLLMCall(msg)


            if not llm_call_successful:
                error_message = str(
                    llm_content) if llm_content else "Unknown LLM error during get_initial_response"
                raise MCPClientRunner.FailedLLMCall(error_message)

            # Assuming llm_content is the actual response data from the model on success
            return {"response": llm_content, "status": "success"}

        except MCPClientRunner.FailedLLMCall as flc:
            msg = f"LLM call failed: {flc}"
            self._log.error(msg)
            return {"error": msg, "type": "FailedLLMCall"}
        except ValueError as ve:
            msg = f"Input error for model response: {ve}"
            self._log.error(msg)
            return {"error": msg, "type": "ValueError"}
        except Exception as e:
            msg = f"An unexpected error occurred while getting model response: {e}"
            self._log.exception(msg)
            return {"error": msg, "type": "Exception"}

    # Removed _get_mcp_responses_and_clarifications as it's no longer needed
    # async def _get_mcp_responses_and_clarifications(self, ...):
    #     ...

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
        Ensures Ollama is ready, and starts the web server.
        """
        self._ensure_ollama_ready()
        self._web_server.run()

    async def run(self) -> None:
        await self._start_services()


async def main() -> None:
    runner = MCPClientRunner()
    await runner.run()

if __name__ == "__main__":
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())
