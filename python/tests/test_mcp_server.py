from typing import Tuple, Protocol, Awaitable, List, Any
import unittest
import asyncio
import socket
import os
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

    _test_number = 0
    _test_number_lock = asyncio.Lock()
    _name: str = ""
    _image: str = ""
    _port: int = -1
    _internal_port: int = 6277
    _error_str: str = "Error"

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
        # Find a free port and also use this to uniquly identify the containers
        cls._port = await asyncio.to_thread(cls._get_free_port)

        # Build and run the MCP test container, picking up the latest mcp server script
        cls._name, cls._image = await asyncio.to_thread(
            cls._build_mcp_test_container)

        # Run the MCP test container
        await asyncio.to_thread(cls._run_mcp_test_container)

        # Wait for the container to be ready
        await asyncio.sleep(5)

    @classmethod
    def tearDownClass(cls):
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
                os.getcwd(), "mcp/environment/prod/build-prod-container.sh")
            if not os.path.exists(build_script):
                build_script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                            "environment/prod/build-prod-container.sh")
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
                os.getcwd(), "mcp/environment/prod/run-prod-container.sh")
            if not os.path.exists(run_script):
                run_script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                          "environment/prod/run-prod-container.sh")
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

        # type: ignore (test_func)
        await asyncio.create_task(self.run_mcp_client_test(_ping_test)) # type: ignore

    async def test_02_list_tools(self):
        async def _list_tools_test(session: ClientSession,
                                   **_: dict[str, Any]) -> None:
            try:
                # Get the list of available tools with a 10-second timeout
                actual_tools: types.ListToolsResult = await asyncio.wait_for(session.list_tools(), timeout=10.0)
                expected_tools: List[str] = ["add", "multiply"]
                actual_tool_names: List[str] = [
                    # type: ignore (tool.name)
                    tool.name for tool in actual_tools.tools]
                self.assertEqual(type(actual_tools), types.ListToolsResult,
                                 f"Expected {types.ListToolsResult} type, but got {type(actual_tools)}")
                self.assertEqual(len(actual_tool_names), len(expected_tools),
                                 f"Expected {len(expected_tools)} tools, but got {len(actual_tool_names)}")
                for expected_tool in expected_tools:
                    self.assertIn(expected_tool, actual_tool_names,
                                  f"Expected tool '{expected_tool}' not found in the list of tools")
            except asyncio.TimeoutError:
                self.fail("List tools operation timed out after 10 seconds")
            except Exception as e:
                self.fail(
                    f"List tools operation failed with exception: {str(e)}")

        # type: ignore (test_func)
        await asyncio.create_task(self.run_mcp_client_test(_list_tools_test)) # type: ignore

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
        ]
        for a, b, expected in test_cases:
            await asyncio.create_task(self.run_mcp_client_test(_add_tool_test, a=a, b=b, expected=expected)) # type: ignore

    @classmethod
    async def run_mcp_client_test(cls,
                                  mcp_client_test: MCPClientTest, **kwargs: dict[str, Any]) -> None:
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
                self.assertTrue(self.is_castable(test_result, expected_type),
                                f"Expected {expected_type} type, but got {type(test_result)}")
                actual_value = expected_type(test_result)
                self.assertEqual(actual_value, expected_value,
                                 f"Expected result {expected_value}, but got {actual_value}")

    @classmethod
    def is_castable(cls,
                    value: Any,
                    target_type: type) -> bool:
        try:
            target_type(value)
            return True
        except (ValueError, TypeError):
            return False


if __name__ == "__main__":
    unittest.main()
