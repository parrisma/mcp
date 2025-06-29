# Standard library imports
import copy
import importlib.util
import json
import logging
import os
import random
import re
import sys
import uuid
from enum import Enum
from typing import Dict, Any, Callable, List, Tuple, Annotated

# Third-party imports
from pydantic import Field

# Local application imports
from i_mcp_server import IMCPServer
from instrument_service.instrument_service import InstrumentService
from static_data_service.static_data_service import StaticDataService
from .report_generator import EquityReportGenerator


class EquityResearchService(IMCPServer):

    class ErrorLoadingResearchConfig(RuntimeError):
        pass

    class ResearchField(Enum):
        TITLE = "title"
        REPORT = "report"
        PUBLISH_DATE = "publish_date"
        RATING = "rating"

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
            EquityResearchService.ConfigField.DB_NAME.value, "EquityResearchService")
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
            EquityResearchService.ConfigField.DB_PATH.value, "./")
        if not os.path.exists(self._db_path):
            raise self.ErrorLoadingResearchConfig(
                f"Config path {self._db_path} does not exist.")

        self._db_name: str = json_config.get(
            EquityResearchService.ConfigField.DB_NAME.value, "research_config.json")
        if not self._db_name:
            raise self.ErrorLoadingResearchConfig(
                "Research Config path name is not specified in the configuration.")

        self._full_db_path = os.path.join(self._db_path, self._db_name)
        if not os.path.exists(self._full_db_path):
            msg = f"Research config file {self._full_db_path} does not exist. Please ensure the path is correct."
            self._log.error(msg)
            raise self.ErrorLoadingResearchConfig(msg)

        self._log.info(
            f"Equity Research Service initialized name: {self._server_name} db: {self._full_db_path}")

        self._research_config: Dict[str, Any] = self._load_research_config()
        if not self._research_config:
            raise self.ErrorLoadingResearchConfig(
                "Research config is empty or could not be loaded.")

        # We embed an instrument service as we need to look up instruments
        # in order to generate research reports.
        instrument_db_path = json_config.get(
            IMCPServer.ConfigFields.AUX_DB_PATH.value, None)
        if not instrument_db_path:
            raise ValueError(
                "Equity Research service - Missing required instrument db path sent via json config as : --aux_db_path")

        instrument_db_name = json_config.get(
            IMCPServer.ConfigFields.AUX_DB_NAME.value, None)
        if not instrument_db_name:
            raise ValueError(
                "Equity Research service - Missing required instrument db name sent via json config as : --aux_db_name")

        self._json_config_research: Dict[str, Any] = dict(json_config)

        config_copy: Dict[str, Any] = copy.deepcopy(self._json_config_research)
        config_copy[InstrumentService.ConfigField.DB_NAME.value] = instrument_db_name
        config_copy[InstrumentService.ConfigField.DB_PATH.value] = instrument_db_path
        self._instrument_service: InstrumentService = InstrumentService(
            logger=self._log,
            json_config=config_copy)
        if not self._instrument_service:
            raise self.ErrorLoadingResearchConfig(
                "Local Instrument Service could not be initialized, which the equity research service needs to function.")

        self._report_generator = EquityReportGenerator(
            research_config_json=self._research_config)

    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def supported_tools(self) -> List[Tuple[str, Callable]]:
        return [("get_all_research_field_names", self.get_all_research_field_names),
                ("get_research", self.get_research)
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

    def _load_research_config(self) -> Dict[str, Any]:
        try:
            with open(self._full_db_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    raise self.ErrorLoadingResearchConfig(
                        "Research config file is empty.")
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    raise self.ErrorLoadingResearchConfig(
                        "Malformed JSON in research config.") from e
                return data
        except Exception as e:
            raise self.ErrorLoadingResearchConfig(
                f"Error loading research config: {str(e)}") from e

    def get_all_research_field_names(self) -> Dict[str, Any]:
        try:
            return {"research_fields": [field.value for field in self.ResearchField.__members__.values()]}
        except Exception as e:
            msg = f"Error retrieving research field names: {str(e)}"
            self._log.error(msg)
            return json.loads(json.dumps({"error": msg}))

    def get_research(self,
                     stock_name: Annotated[str, Field(description="A regular expression for the stock to search for in research reports")]) -> List[Dict[str, Any]]:
        try:
            # Get the instrument details for the stock name
            instrument = self._instrument_service.get_instruments(
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

            research_reports = []
            stock_name = inst.get(
                InstrumentService.InstrumentField.INSTRUMENT_LONG_NAME.value, "system error with instrument record")
            sector = inst.get(
                InstrumentService.InstrumentField.INDUSTRY.value, "system error with instrument record")
            
            # Generate a smaller number of research reports (1-3) compared to news articles
            for _ in range(random.randint(1, 3)):
                research_reports.append(self._report_generator.generate_report(
                    stock_name=stock_name,
                    sector=sector,
                    venue=random.choice(self._venues)
                ))
            return research_reports
        except Exception as e:
            msg = f"Error searching for research reports for [{stock_name}]: {str(e)}"
            self._log.error(msg)
            return [{"error": msg}]


# Allow the file to be run directly for testing
if __name__ == "__main__":
    
    # Add the parent directory to sys.path to allow imports when running directly
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, parent_dir)
    
    # When running directly, use direct import of report_generator
    # instead of relative import
    try:
        # First try to directly import from the local file
        report_generator_path = os.path.join(os.path.dirname(__file__), "report_generator.py")
        if os.path.exists(report_generator_path):
            spec = importlib.util.spec_from_file_location(
                "report_generator",
                report_generator_path
            )
            if spec and spec.loader:
                report_generator = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(report_generator)
                EquityReportGenerator = report_generator.EquityReportGenerator
            else:
                raise ImportError("Failed to load report_generator module")
        else:
            raise ImportError(f"report_generator.py not found at {report_generator_path}")
    except ImportError as e:
        print(f"Import error: {str(e)}")
        sys.exit(1)
    
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("EquityResearchService")
    
    try:
        # Simple configuration for direct testing
        config = {
            "db_name": "research_config.json",
            "db_path": "python/src/server/equity_research_service",
            "server_name": "EquityResearchServiceTest",
            "aux_db_name": "instrument.json",
            "aux_db_path": "python/src/server/instrument_service"
        }
        
        service = EquityResearchService(logger, config)
        print(f"Service initialized successfully: {service.server_name}")
        
        # Test getting field names
        fields = service.get_all_research_field_names()
        print(f"Research fields: {fields}")
        
        # Test with a sample stock if provided
        if len(sys.argv) > 1:
            stock_name = sys.argv[1]
            print(f"Testing with stock: {stock_name}")
            results = service.get_research(stock_name)
            print(f"Results: {json.dumps(results, indent=2)}")
        else:
            print("No stock name provided for testing. Run with: python equity_research_service.py 'Astro Energy'")
            
    except Exception as e:
        logger.error(f"Error running equity research service: {str(e)}")
        print(f"Error: {str(e)}")
