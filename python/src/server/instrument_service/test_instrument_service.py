from typing import List
import logging
import pytest
import httpx
import uuid
import threading
import time
import subprocess
import os
from mcp_client import MCPClient
from mcp_client_web_server import MCPClientWebServer
import asyncio
    
# Configure logging for tests
logger = logging.getLogger("InstrumentServiceTest")
logging.basicConfig(level=logging.DEBUG)

# These custom arguments have to be defined in the conftest.py filem which sits locally to this.

@pytest.fixture(scope="session")
def port(request: pytest.FixtureRequest) -> int:
    return request.config.getoption("--port", default=None)


@pytest.fixture(scope="session")
def host(request: pytest.FixtureRequest) -> str:
    return request.config.getoption("--host", default=None)


@pytest.fixture(scope="session")
def server_name(request: pytest.FixtureRequest) -> str:
    return request.config.getoption("--server-name", default=None)


@pytest.fixture
def instrument_server_client():
    """
    Fixture that provides a function to call the instrument server using MCPClient.

    Returns:
        function: A function that takes instrument server details and command,
                  and executes the request against that server.
    """
    def call_mcp_client(host: str,
                        port: int,
                        server_type: str,
                        command: str,
                        *args,
                        timeout: int = 30):
        """
        Call an MCP client command on the specified instrument server.

        Args:
            host (str): The hostname or IP of the instrument server.
            port (int): The port number of the instrument server.
            command (str): The MCP command to execute (e.g., 'status', 'restart').
            *args: Additional arguments to pass to the command.
            timeout (int): Timeout in seconds for the command.

        Returns:
            tuple: (stdout, stderr, return_code) from the command execution.
        """
        client = MCPClient(server_base_urls=[f"http://{host}:{port}"])

        stdout = ""
        stderr = ""
        return_code = 0

        try:
            if command == "get_instruments":
                field_name = args[0] if len(args) > 0 else "name"
                regex = args[1] if len(args) > 1 else ".*"
                # Since execute_tool is an async method, we need to run it in an event loop

                async def run_execute_tool():
                    return await client.execute_tool(
                        server_name=server_type,
                        tool_name="get_instruments",
                        arguments={"field_name": field_name, "regex": regex}
                    )

                result = asyncio.run(run_execute_tool())
                stdout = str(result)
            # Add other commands as needed
            else:
                stderr = f"Unknown command: {command}"
                return_code = 1
        except Exception as e:
            stderr = str(e)
            return_code = 1

        return stdout, stderr, return_code

    return call_mcp_client


def test_get_instruments(instrument_server_client,
                         host: str,
                         port: int,
                         server_name: str):
    """
    Test that we can retrieve the list of instruments from the instrument server.
    """

    field_name = "name"  # You can change this to any field you want to search by
    regular_expression = ".*"  # This regex will match all instruments
    stdout, stderr, return_code = instrument_server_client(host,
                                                           port,
                                                           server_name,
                                                           "get_instruments",
                                                           field_name,
                                                           regular_expression)

    logger.debug(f"get_instruments stdout: {stdout}")
    if stderr:
        logger.debug(f"get_instruments stderr: {stderr}")

    assert not stderr, f"Expected empty stderr, but got: {stderr}"
    assert "error" not in stdout.lower(), f"Found error in stdout: {stdout}"
