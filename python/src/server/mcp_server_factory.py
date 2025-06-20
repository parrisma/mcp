import logging
from typing import Dict, Any
from i_mcp_server import IMCPServer
from hello_world.hello_world_server import HelloWorldServer
from instrument_service.instrument_service import InstrumentService
from static_data_service.static_data_service import StaticDataService
from client_service.client_service import ClientService
from trade_service.trade_service import TradeService
from news_service.news_service import NewsService
from equity_research_service.equity_research_service import EquityResearchService


class MCPServerFactory:
    """
    A factory class for creating different types of MCP servers.
    """

    def create_server(self, server_type: str, logger: logging.Logger, json_config: Dict[str, Any]) -> IMCPServer:
        """
        Creates and returns an MCP server instance based on the specified type.

        Args:
            server_type: The type of the server to create ('hello_world' or 'instrument').
            logger: The logger instance to pass to the server.
            json_config: The configuration dictionary for the server.

        Returns:
            An instance of the specified MCP server.

        Raises:
            ValueError: If the server_type is not supported.
        """
        if server_type.lower() == 'hello_world':
            return HelloWorldServer(logger, json_config)
        elif server_type.lower() == 'instrument':
            return InstrumentService(logger, json_config)
        elif server_type.lower() == 'static_data':
            return StaticDataService(logger, json_config)
        elif server_type.lower() == 'client':
            return ClientService(logger, json_config)
        elif server_type.lower() == 'trade':
            return TradeService(logger, json_config)
        elif server_type.lower() == 'news':
            return NewsService(logger, json_config)
        elif server_type.lower() == 'equity_research':
            return EquityResearchService(logger, json_config)
        else:
            raise ValueError(f"Unsupported server type: {server_type}")
