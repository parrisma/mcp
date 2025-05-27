from typing import Tuple, Protocol, Awaitable, List, Dict, Any, Callable
import unittest
import asyncio
import socket
import os
import re
import subprocess
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
import mcp.types as types


class TestMCPServer(unittest.IsolatedAsyncioTestCase):

    class MCPClientTest(Protocol):
        async def __call__(self,
                           session: ClientSession,
                           **kwargs: dict[str, Any]
                           ) -> Awaitable[None]: ...

    class MCPGetCapability(Protocol):
        async def __call__(self,
                           session: ClientSession,
                           **kwargs: dict[str, Any]
                           ) -> Awaitable[Any]: ...

    _test_number = 0
    _test_number_lock = asyncio.Lock()
    _name: str = ""
    _image: str = ""
    _port: int = -1
    _internal_port: int = 6277
    _error_str: str = "Error"

    # == SET TO TRUE IF RUNNING MCP_SERVER LOCALLY IN A DEBUG SESSION ==
    # == we then assume mcp-server is on localhost and port 6277      ==
    _local_server: bool = os.environ.get(
        "MCP_LOCAL_SERVER_MODE", "True").lower() == "true"

    @classmethod
    async def get_and_incr_test_number(cls) -> int:
        async with cls._test_number_lock:
            cls._test_number += 1
        return cls._test_number

    @classmethod
    def setUpClass(cls):
        asyncio.run(cls._asyncSetUpClass())

    @classmethod
    async def _asyncSetUpClass(cls):

        if cls._local_server:
            # If running locally, set the port to a fixed value
            cls._port = cls._internal_port
            cls._name = "localhost"
            print(f"Running MCP server locally on port: {cls._port}")
        else:
            # Find a free port and also use this to uniquly identify the containers
            cls._port = await asyncio.to_thread(cls._get_free_port)

            # Build and run the MCP test container, picking up the latest mcp server script
            cls._name, cls._image = await asyncio.to_thread(
                cls._build_mcp_test_container)

            # Run the MCP test container
            await asyncio.to_thread(cls._run_mcp_test_container)

            # Wait for the container to be ready
            await asyncio.sleep(5)

        return

    @classmethod
    def tearDownClass(cls):
        if not cls._local_server:
            asyncio.run(cls._asyncTearDownClass())

    @classmethod
    async def _asyncTearDownClass(cls):
        await asyncio.to_thread(cls.stop_and_remove_mcp_test_container)
        del cls._port

    @classmethod
    def _get_free_port(cls) -> int:
        """
        Find a truly free port by ensuring no conflicts with other tests running in parallel.
        """
        for _ in range(5):  # Retry mechanism in case of conflicts
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', 0))  # Let OS choose a free port
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                port = s.getsockname()[1]

                # Check if the port is still available before returning
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
                    if test_socket.connect_ex(('localhost', port)) != 0:
                        return port  # Port is truly free

        raise RuntimeError(
            "Failed to find a free port after multiple attempts.")

    @classmethod
    def _build_mcp_test_container(cls) -> Tuple[str, str]:
        """
            Helper function to build a test container for the MCP server.
            This is run each time to ensure that the latest version of the
            mcp server (py) script is used.
        """
        # Generate a unique container name for this test run
        container_name = f"mcp-test-server-{cls._port}"
        # Use the same unique name for the image and clean up after the test
        container_image = f"mcp-test-image-{cls._port}"

        try:
            # Build the MCP server container if it doesn't exist
            # This uses the build-prod-container.sh script
            build_script = os.path.join(
                os.getcwd(), "environment/prod/build-prod-container.sh")
            if not os.path.isfile(build_script):
                raise RuntimeError(
                    f"Build script not found: {build_script}, assumes cwd [{os.getcwd()}] is set to the mcp project root")

            subprocess.run([
                build_script,
                "--image", container_image,
                "--name", container_name,
                "--port", str(cls._port)],
                check=True)

            # Check if the image exists
            check_image_cmd = ["docker", "images", "-q", container_image]
            image_exists = subprocess.run(
                check_image_cmd, capture_output=True, check=True).stdout.strip()

            if not image_exists:
                raise RuntimeError(
                    f"Image {container_image} was not built successfully.")

        except Exception as e:
            print(f"Error {e} building container: {container_image}")
            raise
        return (container_name, container_image,)

    @classmethod
    def _run_mcp_test_container(cls) -> str:
        """
            Helper function to run a test container for the MCP server.
            This is run on the given port making the mcp server available
            on the docker mcp-net shared with the dev container in which
            these test are run.
        """

        try:
            # Check if the image exists
            check_image_cmd = ["docker", "images", "-q", cls._image]
            image_exists = subprocess.run(
                check_image_cmd, capture_output=True, check=True).stdout.strip()

            if not image_exists:
                raise RuntimeError(
                    f"Image {cls._image} was not built successfully.")

            # Run the MCP server using the run-prod-container.sh script
            run_script = os.path.join(
                os.getcwd(), "environment/prod/run-prod-container.sh")
            if not os.path.isfile(run_script):
                raise RuntimeError(
                    f"Run script not found: {run_script}, assumes cwd [{os.getcwd()}] is set to the mcp project root")

            subprocess.run([
                run_script,
                "--image", cls._image,
                "--name", cls._name,
                "--host", cls._name,
                "--port", str(cls._port),
                "--internal-port", str(cls._internal_port)],
                check=True)

            check_running_cmd = ["docker", "ps", "--filter",
                                 f"ancestor={cls._image}", "--format", "{{.ID}}"]

            # Run the command
            running_image_id = subprocess.run(
                check_running_cmd, capture_output=True, text=True, check=True).stdout.strip()

            if running_image_id:
                print(
                    f"Image [{cls._image}] is running with ID: [{running_image_id}]")
            else:
                print(f"Image [{cls._image}] is NOT running.")

        except Exception as e:
            print(f"Error {e} running container: {cls._image}")
            raise

        return running_image_id

    @classmethod
    def stop_and_remove_mcp_test_container(cls) -> None:
        try:
            print(f"Stopping container: {cls._name}")
            subprocess.run(["docker", "stop", cls._name], check=True)
            print(f"Removing container: {cls._name}")
            subprocess.run(["docker", "rm", cls._name], check=True)
            print(f"Removing image: {cls._image}")
            subprocess.run(["docker", "rmi", cls._image], check=True)
            print(f"Container {cls._name} stopped and removed.")
        except Exception as e:
            print(
                f"Error {e} stopping & removing container & associated image: {cls._name}")
            raise
        return

    async def test_01_ping(self):
        async def _ping_test(session: ClientSession,
                             **_: dict[str, Any]) -> None:
            try:
                # Set a 10-second timeout for the ping operation
                response = await asyncio.wait_for(session.send_ping(), timeout=10.0)
                # Assert that we got a valid response
                self.assertIsNotNone(
                    response, "Ping response should not be None")
            except asyncio.TimeoutError:
                self.fail(
                    "Ping test timed out after 10 seconds - no response received")
            except Exception as e:
                self.fail(f"Ping test failed with exception: {str(e)}")

        await asyncio.create_task(self._run_mcp_client_test(_ping_test)  # type: ignore
                                  )

    async def test_02_list_tools(self):
        async def _list_tools_test(session: ClientSession,
                                   **_: dict[str, Any]) -> None:
            async def _get_tools(session: ClientSession, **_: dict[str, Any]) -> Any:
                return await session.list_tools()

            # Check the capability of the server
            await self._check_capability(session=session,
                                         mcp_get_capability=_get_tools,
                                         capability_type=types.ListToolsResult,
                                         expected_capabilities=[
                                             {"name": "add"},
                                             {"name": "multiply"}],
                                         get_capabilities=lambda x: x.tools,
                                         get_capability_detail=lambda x: {"name": x.name})

        await asyncio.create_task(self._run_mcp_client_test(_list_tools_test)  # type: ignore
                                  )

    async def test_03_add_tool(self):
        async def _add_tool_test(session: ClientSession,
                                 a: Any,
                                 b: Any,
                                 expected: Any) -> None:
            try:
                # Get the list of available tools with a 10-second timeout
                sum_result: types.CallToolResult = await asyncio.wait_for(session.call_tool(
                    name="add",
                    arguments={"a": a, "b": b}
                ), timeout=10.0)
                self._check_call_tool_result(
                    sum_result,
                    num_expected=1,
                    expected_result_types=[types.TextContent],
                    expected_types=[int],
                    expected_values=[expected]
                )

            except asyncio.TimeoutError:
                self.fail("Tool [add] operation timed out after 10 seconds")
            except Exception as e:
                self.fail(
                    f"Tool [add] operation failed with exception: {str(e)}")

        # Test cases with different integer values
        test_cases: List[Tuple[Any, Any, Any]] = [
            (5, 7, 12),         # Positive numbers
            (-3, 8, 5),         # Mixed positive and negative
            (-10, -5, -15),     # Negative numbers
            (0, 0, 0),          # Zeros
            (1000, 2000, 3000),  # Large numbers
            (5.1, 3, self._error_str),  # Error, as float is not castable to int
            (5, 3.9, self._error_str),  # Error, as float is not castable to int
            (5, None, self._error_str),  # Error, as None is passed.
        ]
        for a, b, expected in test_cases:
            await asyncio.create_task(self._run_mcp_client_test(_add_tool_test,  # type: ignore
                                                                a=a,
                                                                b=b,
                                                                expected=expected))
        return

    async def test_04_multiply_tool(self):
        async def _multiply_tool_test(session: ClientSession,
                                      a: Any,
                                      b: Any,
                                      expected: Any) -> None:
            try:
                # Get the list of available tools with a 10-second timeout
                multiply_result: types.CallToolResult = await asyncio.wait_for(session.call_tool(
                    name="multiply",
                    arguments={"a": a, "b": b}
                ), timeout=10.0)
                self._check_call_tool_result(
                    multiply_result,
                    num_expected=1,
                    expected_result_types=[types.TextContent],
                    expected_types=[int],
                    expected_values=[expected]
                )

            except asyncio.TimeoutError:
                self.fail(
                    "Tool [multiply] operation timed out after 10 seconds")
            except Exception as e:
                self.fail(
                    f"Tool [multiply] operation failed with exception: {str(e)}")

        # Test cases with different integer values
        test_cases: List[Tuple[Any, Any, Any]] = [
            (5, 7, 35),         # Positive numbers
            (-3, 8, -24),       # Mixed positive and negative
            (-10, -5, 50),      # Negative numbers
            (0, 5, 0),          # Zero multiplied by a number
            (5, 0, 0),          # Number multiplied by zero
            (10, 100, 1000),    # Large numbers
            (5.1, 3, self._error_str),  # Error, as float is not castable to int
            (5, 3.9, self._error_str),  # Error, as float is not castable to int
        ]
        for a, b, expected in test_cases:
            # type: ignore
            await asyncio.create_task(self._run_mcp_client_test(_multiply_tool_test,  # type: ignore
                                                                a=a,
                                                                b=b,
                                                                expected=expected))
        return

    async def test_05_list_resources(self):
        async def _list_resource_test(session: ClientSession,
                                      **_: dict[str, Any]) -> None:
            async def _get_resources(session: ClientSession, **_: dict[str, Any]) -> Any:
                return await session.list_resources()

            # Check the capability of the server
            await self._check_capability(session=session,
                                         mcp_get_capability=_get_resources,
                                         capability_type=types.ListResourcesResult,
                                         expected_capabilities=[
                                             {"name": "alive", "uri": "alive://"}],
                                         get_capabilities=lambda x: x.resources,
                                         get_capability_detail=lambda x: {"name": x.name, "uri": str(x.uri)})

        await asyncio.create_task(self._run_mcp_client_test(_list_resource_test)  # type: ignore
                                  )

    async def test_06_list_resource_templates(self):
        async def _list_resource_templates_test(session: ClientSession,
                                                **_: dict[str, Any]) -> None:
            async def _get_resource_templates(session: ClientSession, **_: dict[str, Any]) -> Any:
                return await session.list_resource_templates()

            # Check the capability of the server
            await self._check_capability(session=session,
                                         mcp_get_capability=_get_resource_templates,
                                         capability_type=types.ListResourceTemplatesResult,
                                         expected_capabilities=[
                                             {"uriTemplate": "message://{name}"}],
                                         get_capabilities=lambda x: x.resourceTemplates,
                                         get_capability_detail=lambda x: {"uriTemplate": x.uriTemplate})

        await asyncio.create_task(self._run_mcp_client_test(_list_resource_templates_test)  # type: ignore
                                  )

    async def test_07_list_prompts(self):
        async def _list_prompt_test(session: ClientSession,
                                    **_: dict[str, Any]) -> None:
            async def _get_prompts(session: ClientSession, **_: dict[str, Any]) -> Any:
                return await session.list_prompts()

            # Check the capability of the server
            await self._check_capability(session=session,
                                         mcp_get_capability=_get_prompts,
                                         capability_type=types.ListPromptsResult,
                                         expected_capabilities=[
                                             {"name": "sme"}],
                                         get_capabilities=lambda x: x.prompts,
                                         get_capability_detail=lambda x: {"name": x.name})

        await asyncio.create_task(self._run_mcp_client_test(_list_prompt_test)  # type: ignore
                                  )

    async def test_08_test_prompts(self):
        async def _prompt_test(session: ClientSession,
                               **kwargs: dict[str, Any]) -> None:
            async def _call_prompt(session: ClientSession,
                                   **kwargs: dict[str, Any]) -> Any:
                response: types.GetPromptResult
                try:
                    response = await session.get_prompt(
                        name=str(kwargs["name"]),
                        arguments=kwargs["arguments"]
                    )
                except Exception as e:
                    response = types.GetPromptResult(
                        description="Error, failed to get prompt, see repsonsec content",
                        messages=[
                            types.PromptMessage(
                                    role="user",
                                    content=types.TextContent(
                                        type="text", text=str(e))
                            )])
                return response

            cases = [
                ["coding", "MCP Servers"],
                ["math", "pythagorean theorem"],
                ["writing", "beatnik poetry"],
                ["history", "World War II"]  # Error case
            ]

            prompt_test_cases: List[Dict[str, Any]] = [
                {
                    "name": "sme",
                    "arguments": {
                        "topic": cases[0][0],
                        "subject": cases[0][1]
                    },
                    "expected_capabilities": [
                        {"text": re.compile(
                            rf".*you are an expert programmer.*{re.escape(cases[0][1])}.*", re.IGNORECASE)}
                    ]
                },
                {
                    "name": "sme",
                    "arguments": {
                        "topic": cases[1][0],
                        "subject": cases[1][1]
                    },
                    "expected_capabilities": [
                        {"text": re.compile(
                            rf".*you are a high school mathematics.*{re.escape(cases[1][1])}.*", re.IGNORECASE)}
                    ]
                },
                {
                    "name": "sme",
                    "arguments": {
                        "topic": cases[2][0],
                        "subject": cases[2][1]
                    },
                    "expected_capabilities": [
                        {"text": re.compile(
                            rf".*you are a professional writer.*{re.escape(cases[2][1])}.*", re.IGNORECASE)}
                    ]
                },
                {
                    "name": "sme",
                    "arguments": {
                        "topic": cases[3][0],
                        "subject": cases[3][1]
                    },
                    "expected_capabilities": [
                        {"text": re.compile(r".*Error.*", re.IGNORECASE)}
                    ]
                }
            ]

            # Check the behavior of the prompts
            for test_case in prompt_test_cases:
                # Unpack the test case
                case_name = test_case["name"]
                case_args = test_case["arguments"]
                expected_capabilities = test_case["expected_capabilities"]

                # Check the capability of the server
                await self._check_capability(
                    session=session,
                    mcp_get_capability=_call_prompt,
                    capability_type=types.GetPromptResult,
                    expected_capabilities=expected_capabilities,
                    get_capabilities=lambda x: x.messages,
                    get_capability_detail=lambda x: {
                        "text": x.content.text
                    },
                    name=case_name,  # type: ignore
                    arguments=case_args
                )

        await asyncio.create_task(self._run_mcp_client_test(_prompt_test  # type: ignore
                                                            )
                                  )
        return
    #
    # ========== T E S T  U T I L S  ==========
    #

    @classmethod
    async def _run_mcp_client_test(cls,
                                   mcp_client_test: MCPClientTest,
                                   **kwargs: dict[str, Any]) -> None:
        # Connect to the server using SSE, we use container name as host as it is host name on Docker network
        server_url = f"http://{cls._name}:{cls._internal_port}/sse"
        print(f"Connecting to MCP server at: {server_url}")

        # Initialize SSE client connection using async with
        async with sse_client(server_url) as (read_stream, write_stream):
            # Create session using async with
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the session
                await session.initialize()
                await asyncio.sleep(1)

                # Run the test, the test will raise errors if it fails
                tst_num = await cls.get_and_incr_test_number()
                print("=" * 80)
                print(
                    f"Running test   #[{tst_num}] for [{getattr(mcp_client_test, '__name__', str(mcp_client_test))}] on mcp session: [{id(session)}]")
                if kwargs:
                    print(
                        f"Test arguments # {', '.join(f'{k}={v!r}' for k, v in kwargs.items())}")
                await mcp_client_test(session, **kwargs)
                print(
                    f"Completed Test #[{tst_num}] for [{getattr(mcp_client_test, '__name__', str(mcp_client_test))}] on mcp session: [{id(session)}]")
                print("=" * 80)

                return

    def _check_call_tool_result(self,
                                actual: Any,
                                num_expected: int,
                                expected_result_types: List[type],
                                expected_types: List[type],
                                expected_values: List[Any]) -> None:
        if not (len(expected_result_types) == len(expected_types) == len(expected_values)):
            raise ValueError(
                f"Expected result types, values and expected types must all be the same length: {len(expected_result_types)}, {len(expected_types)}, {len(expected_values)}")
        self.assertEqual(type(actual), types.CallToolResult,
                         f"Expected {types.CallToolResult} type, but got {type(actual)}")
        self.assertTrue(isinstance(actual.content, List),
                        f"Expected {List} type, but got {type(actual.content)}")
        self.assertEqual(len(actual.content), num_expected,
                         f"Expected one result but got {len(actual.content)}")
        for result, expected_result_type, expected_type, expected_value in zip(actual.content, expected_result_types, expected_types, expected_values):
            self.assertEqual(type(result), expected_result_type,
                             f"Expected {expected_result_type} type, but got {type(result)}")
            if expected_result_type == types.TextContent:
                test_result: str = result.text
            elif expected_result_type == types.ImageContent:
                assert False, f"Unit tests do not yet handle: {types.ImageContent}"
            elif expected_result_type == types.EmbeddedResource:
                assert False, f"Unit tests do not yet handle: {types.EmbeddedResource}"
            else:
                assert False, f"Unknown result type: {expected_result_type}"
            if expected_value == self._error_str:
                self.assertIn(self._error_str, test_result,
                              f"Expected error string '{self._error_str}' in result, but got {test_result}")
            else:
                self.assertTrue(self._is_castable(test_result, expected_type),
                                f"Expected {expected_type} type, but got {type(test_result)}")
                actual_value = expected_type(test_result)
                self.assertEqual(actual_value, expected_value,
                                 f"Expected result {expected_value}, but got {actual_value}")

    @classmethod
    def _is_castable(cls,
                     value: Any,
                     target_type: type) -> bool:
        try:
            target_type(value)
            return True
        except (ValueError, TypeError):
            return False

    async def _check_capability(self,
                                session: ClientSession,
                                mcp_get_capability: MCPGetCapability,
                                capability_type: type,
                                expected_capabilities: List[Dict[str, Any]],
                                get_capabilities: Callable[[Any], Any],
                                get_capability_detail: Callable[[Any], Dict[str, Any]],
                                **kwargs: dict[str, Any]) -> None:
        try:
            # Get the capability list with a 10-second timeout
            actual_capability = await asyncio.wait_for(mcp_get_capability(session=session,
                                                                          **kwargs), timeout=10.0
                                                       )
            self.assertEqual(type(actual_capability), capability_type,
                             f"Expected {capability_type} type, but got {type(actual_capability)}")

            # Get all capability details as dictionaries
            actual_capability_details: List[Dict[str, Any]] = []
            for capability in get_capabilities(actual_capability):
                actual_capability_details.append(
                    get_capability_detail(capability))

            self.assertEqual(len(actual_capability_details), len(expected_capabilities),
                             f"Expected {len(expected_capabilities)} capabilities, but got {len(actual_capability_details)}")

            for expected, actual in zip(expected_capabilities, actual_capability_details):
                for key, expected_value in expected.items():
                    actual_value = actual.get(key)
                    if isinstance(expected_value, re.Pattern):
                        self.assertIsNotNone(
                            actual_value, f"Missing key '{key}' in actual capability details")
                        self.assertRegex(str(actual_value), expected_value,
                                         f"Value for key '{key}' does not match expected pattern")
                    else:
                        self.assertEqual(
                            actual_value, expected_value, f"Value for key '{key}' does not match: expected {expected_value}, got {actual_value}")
        except asyncio.TimeoutError:
            self.fail(
                "Get capabilities from MCP Server - operation timed out after 10 seconds")
        except (KeyError, AttributeError, ValueError, ConnectionError, socket.error) as e:
            self.fail(
                f"Get capabilities from MCP Server - failed with exception: {str(e)}")


if __name__ == "__main__":
    unittest.main()
