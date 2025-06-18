from turtle import st
from typing import Dict, Any, Callable, List, Tuple, Annotated
from pydantic import Field
import copy
import logging
import re
import uuid
import json
import os
from i_mcp_server import IMCPServer
from enum import Enum
from static_data_service.static_data_service import StaticDataService
from .article_generator import NewsArticleGenerator
from instrument_service.instrument_service import InstrumentService
import random


class NewsService(IMCPServer):

    class ErrorLoadingNewsConfig(RuntimeError):
        pass

    class NewsField(Enum):
        HEADLINE = "headline"
        ARTICLE = "article"
        PUBLISH_TIME = "publish_time"

    class ConfigField(Enum):
        SERVER_NAME = "server_name"
        DB_PATH = IMCPServer.ConfigFields.DATA_PATH.value
        DB_NAME = "db_name"

    def __init__(self,
                 logger: logging.Logger,
                 json_config: Dict[str, Any]) -> None:
        self._log: logging.Logger = logger
        self._config: Dict[str, Any] = json_config

        self._base_name = json_config.get(
            NewsService.ConfigField.DB_NAME.value, "NewsService")
        self._server_name: str = f"{self._base_name}{str(uuid.uuid4()).upper()}"

        self._staticDataService: StaticDataService = StaticDataService(
            logger, json_config)
        self._venue_codes = self._staticDataService.get_all_venue_codes().get(
            self._staticDataService.StaticField.VENUE.value, None)
        self._venues = []
        if self._venue_codes:
            for venue_code in self._venue_codes:
                self._venues.append(
                    self._staticDataService.get_venue_description(code=venue_code).get(self._staticDataService.StaticField.VENUE_DESCRIPTION.value, "Unknown Venue"))

        self._db_path: str = json_config.get(
            NewsService.ConfigField.DB_PATH.value, "./")
        if not os.path.exists(self._db_path):
            raise self.ErrorLoadingNewsConfig(
                f"Config path {self._db_path} does not exist.")

        self._db_name: str = json_config.get(
            NewsService.ConfigField.DB_NAME.value, "news_config.json")
        if not self._db_name:
            raise self.ErrorLoadingNewsConfig(
                "News Config path name is not specified in the configuration.")

        self._full_db_path = os.path.join(self._db_path, self._db_name)
        if not os.path.exists(self._full_db_path):
            msg = f"News config file {self._full_db_path} does not exist. Please ensure the path is correct."
            self._log.error(msg)
            raise self.ErrorLoadingNewsConfig(msg)

        self._log.info(
            f"News Service initialized name: {self._server_name} db: {self._full_db_path}")

        self._news_config: Dict[str, Any] = self._load_news_config()
        if not self._news_config:
            raise self.ErrorLoadingNewsConfig(
                "News config is empty or could not be loaded.")

        # We embed am instrument service as we need to look up instruments
        # in order to generate news articles.
        # In a full implementation the news service would talk over MCP or REST, but as a demo we don't have time for that yet.
        instrument_db_path = json_config.get(
            IMCPServer.ConfigFields.AUX_DB_PATH.value, None)
        if not instrument_db_path:
            raise ValueError(
                "News service - Missing required instrument db path sent via json conifig as : --aux_db_path")

        instrument_db_name = json_config.get(
            IMCPServer.ConfigFields.AUX_DB_NAME.value, None)
        if not instrument_db_name:
            raise ValueError(
                "News service - Missing required instrument db name sent via json conifig as : --aux_db_name")

        self._json_config_news: Dict[str, Any] = dict(json_config)

        config_copy: Dict[str, Any] = copy.deepcopy(self._json_config_news)
        config_copy[InstrumentService.ConfigField.DB_NAME.value] = instrument_db_name
        config_copy[InstrumentService.ConfigField.DB_PATH.value] = instrument_db_path
        self._instrumnt_service: InstrumentService = InstrumentService(
            logger=self._log,
            json_config=config_copy)
        if not self._instrumnt_service:
            raise self.ErrorLoadingNewsConfig(
                "Local Instrument Service could not be initialized, which news servce needs to function.")

        self._article_generator: NewsArticleGenerator = NewsArticleGenerator(
            news_config_json=self._news_config)

    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def supported_tools(self) -> List[Tuple[str, Callable]]:
        return [("get_all_news_field_names", self.get_all_news_field_names),
                ("get_news", self.get_news)
                ]

    @property
    def supported_resources(self) -> List[Tuple[str, Callable]]:
        return []

    @property
    def supported_prompts(self) -> List[Tuple[str, Callable]]:
        return []

    def handle_request(self, request):
        # Implement this method as required by IMCPServer
        raise NotImplementedError("handle_request must be implemented.")

    def _load_news_config(self) -> Dict[str, Any]:
        try:
            with open(self._full_db_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    raise self.ErrorLoadingNewsConfig(
                        "News config file is empty.")
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    raise self.ErrorLoadingNewsConfig(
                        "Malformed JSON in news config.") from e
                return data
        except Exception as e:
            raise self.ErrorLoadingNewsConfig(
                f"Error loading news config: {str(e)}") from e

    def get_all_news_field_names(self) -> Dict[str, Any]:
        try:
            return {"news_fields": [field.value for field in self.NewsField.__members__.values()]}
        except Exception as e:
            msg = f"Error retrieving news field names: {str(e)}"
            self._log.error(msg)
            return json.loads(json.dumps({"error": msg}))

    def get_news(self,
                 stock_name: Annotated[str, Field(description="A regular express for the stock to search for in news articles")]) -> List[Dict[str, Any]]:
        try:
            # Get the instrument details for the stock name
            instrument = self._instrumnt_service.get_instruments(
                field_name=InstrumentService.InstrumentField.INSTRUMENT_LONG_NAME.value,
                regular_expression=stock_name)

            if "error" in instrument:
                raise ValueError(
                    f"Error searching for instruments for stock pattern [{stock_name}]: {instrument['error']}")

            instruments = instrument.get("instruments", None)
            if not instruments or len(instruments) == 0:
                msg = f"No instruments found for stock name [{stock_name}]."
                self._log.error(msg)
                return [{"error": msg}]

            if len(instruments) > 1:
                instrument_names = [inst.get(
                    InstrumentService.InstrumentField.INSTRUMENT_LONG_NAME.value, "Unknown") for inst in instruments]
                msg = (f"Multiple instruments found for stock name [{stock_name}]: {len(instruments)}. "
                       f"Instrument names: {', '.join(instrument_names)}. Please refine your search.")
                self._log.error(msg)
                return [{"error": msg}]

            inst = instruments[0]

            news = []
            stock_name = inst.get(
                InstrumentService.InstrumentField.INSTRUMENT_LONG_NAME.value, "system error with instrument record")
            sector = inst.get(
                InstrumentService.InstrumentField.INDUSTRY.value, "system error with instrument record")
            for _ in range(random.randint(2, 10)):
                news.append(self._article_generator.generate_article(
                    stock_name=stock_name,
                    sector=sector,
                    venue=random.choice(self._venues)
                ))
            return news
        except Exception as e:
            msg = f"Error searching for news article for [{stock_name}]: {str(e)}"
            self._log.error(msg)
            return [{"error": msg}]
