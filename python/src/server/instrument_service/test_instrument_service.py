from re import I
from typing import List
import logging
from urllib import response
import pytest
from sympy import asec
from mcp_client import MCPClient
from mcp_client_web_server import MCPClientWebServer
import asyncio
import json
import ast

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
                        arguments={"field_name": field_name,
                                   "regular_expression": regex}
                    )

                result = asyncio.run(run_execute_tool())
                stdout = str(result)
            # Add other commands as needed
            elif command == "get_all_instrument_field_names":
                async def run_execute_tool():
                    return await client.execute_tool(
                        server_name=server_type,
                        tool_name="get_all_instrument_field_names",
                        arguments={}
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


def test_get_all_instrument_field_names(instrument_server_client,
                                        host: str,
                                        port: int,
                                        server_name: str):
    stdout, stderr, return_code = instrument_server_client(host,
                                                           port,
                                                           server_name,
                                                           "get_all_instrument_field_names")

    expected_fields = ["GUID",
                       "Instrument_Long_Name",
                       "Reuters_Code",
                       "SEDOL",
                       "ISIN",
                       "Product_Type",
                       "Industry",
                       "Currency",
                       "Listing_Date"]

    logger.debug(f"get_instruments stdout: {stdout}")
    if stderr:
        logger.debug(f"get_instruments stderr: {stderr}")

    assert not stderr, f"Expected empty stderr, but got: {stderr}"
    assert "error" not in stdout.lower(), f"Found error in stdout: {stdout}"
    result = json.loads(json.dumps(ast.literal_eval(stdout)))
    assert len(result['results']
               ) == 2, "Expected source details and a single response"
    response = result['results'][1]['response']
    assert isinstance(
        response, list), "Expected a single instrument as exact match"
    assert response[0].get(
        'instrument_fields', None) != None, "Expected an instrument set of values"
    instrument_fields = response[0]["instrument_fields"]
    assert isinstance(instrument_fields,
                      list), "Expected a list of instrument fields"
    assert len(instrument_fields) == len(
        expected_fields), f"Expected {len(expected_fields)} field types: {expected_fields}"
    for field in expected_fields:
        assert field in instrument_fields, f"Missing field name {field}"


def test_get_instrument(instrument_server_client,
                        host: str,
                        port: int,
                        server_name: str):
    """
    Test that we can retrieve an instruments from the instrument server.
    """

    field_name = "SEDOL"  # You can change this to any field you want to search by
    sedol = "B61523XYZ"
    regular_expression = f".*{sedol}.*"  # From instrument.json
    stdout, stderr, return_code = instrument_server_client(host,
                                                           port,
                                                           server_name,
                                                           "get_instruments",
                                                           field_name,
                                                           regular_expression)

    expected_instrument = {"GUID": "f19bb0db-d1f7-443a-b2a8-1dc650208890",
                           "Instrument_Long_Name": "Astro Energy",
                           "Reuters_Code": "PNVJ.K",
                           "SEDOL": "B61523XYZ",
                           "ISIN": "JP0000020272345",
                           "Product_Type": "EQ",
                           "Industry": "Aerospace",
                           "Currency": "EUR",
                           "Listing_Date": "1994-10-19"}

    logger.debug(f"get_instruments stdout: {stdout}")
    if stderr:
        logger.debug(f"get_instruments stderr: {stderr}")

    assert not stderr, f"Expected empty stderr, but got: {stderr}"
    assert "error" not in stdout.lower(), f"Found error in stdout: {stdout}"
    result = json.loads(json.dumps(ast.literal_eval(stdout)))
    assert len(result['results']
               ) == 2, "Expected source details and a single response"
    response = result['results'][1]['response']
    assert isinstance(
        response, list), "Expected a single instrument as exact match"
    assert response[0].get(
        'instruments', None) != None, "Expected an instrument set of values"
    instruments = response[0]['instruments']
    assert isinstance(instruments, list), "Expected a list of (1) instruments"
    assert len(instruments) == 1, "Expected a single instrument"
    instrument = instruments[0]
    for k, v in instrument.items():
        assert instrument.get(
            k, None) != None, f"Missing instrument detail for {k}"
        assert instrument[k] == v, f"expected field {k} to have value {v} but got {instrument[k]}"
