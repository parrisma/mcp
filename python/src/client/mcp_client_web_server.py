from operator import call
from typing import Dict, Protocol, Any, Literal, List
from functools import partial, update_wrapper
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import json
from enum import Enum
import signal
import sys
import threading
import logging


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
        self._log: logging.Logger = self._configure_logging()
        self._app = Flask(__name__)
        CORS(self._app, resources={r"/*": {"origins": f"http://localhost:*"}})
        self._host: str = host
        self._port: int = port
        self._log.debug(f"Client Web Server starting on {host}:{port}")
        self._routes: Dict[str, MCPClientWebServer.WebCallback] = {}
        self._app.route('/')(self._home)

        self._messages: Dict[str, str] = {}

    def _configure_logging(self) -> logging.Logger:
        log: logging.Logger = logging.getLogger("MessageWebServer")
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler()]
            )
        return log

    def _home(self) -> Response:
        self._log.debug("Home page requested")

        html = "<html><head><title>Client Service - Available Routes</title></head><body>"
        html += "<h1>Available Routes</h1><ul>"
        for route in self._routes:
            func_name: str = getattr(
                self._routes[route], "__name__", "unknown")
            html += f"<li><a href='{route}'>{route}</a> - {func_name}</li>"
        html += "</ul></body></html>"

        self._log.debug(f"Home page generated with {len(self._routes)} routes")
        return Response(html, mimetype="text/html")

    def _web_user_callback_wrapper(self,
                                   callback: "MCPClientWebServer.WebUserCallback") -> Response:
        self._log.debug(
            f"Processing {request.method} request to {request.path}")

        query_params: Dict[str, Any] = {}
        query_params[self.QueryParamKeys.PATH.value] = request.path

        # Handle both GET and POST parameters
        # Handle both GET and POST parameters
        args_dict: Dict[str, Any] = request.args.to_dict()
        self._log.debug(f"Initial args from query string: {args_dict}")

        # If this is a POST request with JSON body, use the JSON data directly for args
        if request.method == 'POST' and request.is_json:
            json_data = request.get_json()
            self._log.debug(f"Received JSON data: {json_data}")
            if isinstance(json_data, dict):
                args_dict = json_data  # Use JSON data directly
                self._log.debug(f"Using JSON data as args: {args_dict}")

        query_params[self.QueryParamKeys.ARGS.value] = args_dict
        self._log.debug(f"Final query params: {query_params}")

        try:
            result: Dict[str, Any] = call(callback, query_params)
            self._log.debug(f"Callback result: {result}")
            return jsonify(result)
        except Exception as e:
            self._log.error(f"Error in callback execution: {str(e)}")
            error_response = jsonify({"error": str(e)})
            error_response.status_code = 500
            return error_response

    def add_route(self,
                  route: str,
                  methods: List[Literal['GET', 'POST', 'PUT', 'DELETE']],
                  handler: "MCPClientWebServer.WebUserCallback") -> None:
        self._log.debug(f"Adding route: {route} with methods: {methods}")

        wrapped_callback: MCPClientWebServer.WebCallback = partial(
            self._web_user_callback_wrapper, callback=handler)
        update_wrapper(wrapped_callback, handler)

        self._app.route(route)(wrapped_callback)
        self._routes[route] = wrapped_callback
        self._app.add_url_rule(
            route, view_func=self._routes[route], methods=methods)

        self._log.debug(
            f"Route {route} successfully registered with methods: {methods}")

    def shutdown_server(self):
        # This function is designed to be called from a request handler
        # to shut down the Werkzeug server.
        self._log.debug("Shutdown request received")

        shutdown = request.environ.get('werkzeug.server.shutdown')
        if shutdown is None:
            self._log.error(
                "Not running with the Werkzeug Server - cannot shutdown")
            raise RuntimeError('Not running with the Werkzeug Server')

        self._log.info("Shutting down server...")
        shutdown()
        return 'Server shutting down...'

    def run(self) -> None:
        self._log.info(
            f"Starting MCPClientWebServer on {self._host}:{self._port}")

        # Signal handler for graceful shutdown
        def signal_handler(sig, frame):
            self._log.info(f"Received signal {sig}, shutting down server...")
            # In a real application, you might want to do more cleanup here
            sys.exit(0)

        # Only register signal handlers if this is the main thread
        if threading.current_thread() is threading.main_thread():
            self._log.debug(
                "Registering signal handlers for graceful shutdown")
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        else:
            self._log.warning(
                "Not registering signal handlers in non-main thread")

        # Add a shutdown route (optional, mainly for testing)
        self._log.debug("Adding shutdown route")
        self._app.route('/shutdown')(self.shutdown_server)

        try:
            self._log.info(
                f"Flask server starting on {self._host}:{self._port}")
            self._app.run(host=self._host, port=self._port)
        except Exception as e:
            self._log.error(f"Error running Flask server: {str(e)}")
            raise
        finally:
            # This block might not always be reached on abrupt termination,
            # but it's good practice for cleaner exits.
            self._log.info("Flask server process finished.")
