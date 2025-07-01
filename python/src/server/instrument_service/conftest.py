def pytest_addoption(parser):
    parser.addoption("--server-name", action="store",
                     help="Name of the Instrument service")
    parser.addoption("--port", action="store", help="Port to connect to")
    parser.addoption("--host", action="store", help="Host to connect to")
