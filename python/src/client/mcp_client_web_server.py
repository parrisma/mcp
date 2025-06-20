from operator import call
from typing import Dict, Protocol, Any, Literal, List
from functools import partial, update_wrapper
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import json
from enum import Enum
import signal
import sys


class MCPClientWebServer:

    class QueryParamKeys(Enum):
        PATH = "path"
        ARGS = "args"

        def __str__(self) -> str:
            return self.value

    class WebUserCallback(Protocol):
        def __call__(self, params: Dict) -> Dict: ...

    class WebCallback(Protocol):
        def __call__(self) -> Response: ...

    def __init__(self,
                 host: str,
                 port: int) -> None:
        self._app = Flask(__name__)
        CORS(self._app, resources={r"/*": {"origins": f"http://localhost:*"}})
        self._host: str = host
        self._port: int = port
        self._routes: Dict[str, MCPClientWebServer.WebCallback] = {}
        self._app.route('/')(self._home)

        self._messages: Dict[str, str] = {}

    def _home(self) -> Response:
        html = "<html><head><title>Client Service - Available Routes</title></head><body>"
        html += "<h1>Available Routes</h1><ul>"
        for route in self._routes:
            func_name: str = getattr(
                self._routes[route], "__name__", "unknown")
            html += f"<li><a href='{route}'>{route}</a> - {func_name}</li>"
        html += "</ul></body></html>"
        return Response(html, mimetype="text/html")

    def _web_user_callback_wrapper(self,
                                   callback: "MCPClientWebServer.WebUserCallback") -> Response:
        query_params: Dict[str, Any] = {}
        query_params[self.QueryParamKeys.PATH.value] = request.path

        # Handle both GET and POST parameters
        # Handle both GET and POST parameters
        args_dict: Dict[str, Any] = request.args.to_dict()

        # If this is a POST request with JSON body, use the JSON data directly for args
        if request.method == 'POST' and request.is_json:
            json_data = request.get_json()
            if isinstance(json_data, dict):
                args_dict = json_data  # Use JSON data directly

        query_params[self.QueryParamKeys.ARGS.value] = args_dict
        result: Dict[str, Any] = call(callback, query_params)
        return jsonify(result)

    def add_route(self,
                  route: str,
                  methods: List[Literal['GET', 'POST', 'PUT', 'DELETE']],
                  handler: "MCPClientWebServer.WebUserCallback") -> None:
        wrapped_callback: MCPClientWebServer.WebCallback = partial(
            self._web_user_callback_wrapper, callback=handler)
        update_wrapper(wrapped_callback, handler)
        self._app.route(route)(wrapped_callback)
        self._routes[route] = wrapped_callback
        self._app.add_url_rule(
            route, view_func=self._routes[route], methods=methods)

    def shutdown_server(self):
        # This function is designed to be called from a request handler
        # to shut down the Werkzeug server.
        shutdown = request.environ.get('werkzeug.server.shutdown')
        if shutdown is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        shutdown()
        return 'Server shutting down...'

    def run(self) -> None:
        # Signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print(f"Received signal {sig}, shutting down server...")
            # In a real application, you might want to do more cleanup here
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Add a shutdown route (optional, mainly for testing)
        self._app.route('/shutdown')(self.shutdown_server)

        try:
            self._app.run(host=self._host, port=self._port)
        finally:
            # This block might not always be reached on abrupt termination,
            # but it's good practice for cleaner exits.
            print("Flask server process finished.")


if __name__ == '__main__':

    class TestCallback:
        def any_callback(self,
                         params: Dict) -> Dict:
            params_as_json: str = json.dumps(params)
            return {"message": f"This is a test callback response at {request.full_path} with params: {params_as_json}"}

    test_callback = TestCallback()
    client = MCPClientWebServer(host='0.0.0.0', port=5000)
    methods: List[str] = ['GET', 'POST']
    route = '/test'
    client.add_route(route=route,
                     methods=['GET', 'POST'],
                     handler=test_callback.any_callback)
    client.run()
