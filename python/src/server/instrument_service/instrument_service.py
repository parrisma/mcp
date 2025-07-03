from typing import Dict, Any, Callable, List, Tuple, Annotated
from httpx import get
from pydantic import Field
import logging
import re
import uuid
import json
import os
import random
from i_mcp_server import IMCPServer
from enum import Enum
from static_data_service.static_data_service import StaticDataService
from .tickers import get_instr_tickers


class InstrumentService(IMCPServer):

    class ErrorLoadingInstrumentDatabase(RuntimeError):
        pass

    class InstrumentField(Enum):
        GUID = "GUID"
        INSTRUMENT_LONG_NAME = "Instrument_Long_Name"
        REUTERS_CODE = "Reuters_Code"
        SEDOL = "SEDOL"
        ISIN = "ISIN"
        PRODUCT_TYPE = "Product_Type"
        INDUSTRY = "Industry"
        CURRENCY = "Currency"
        LISTING_DATE = "Listing_Date"

    class ConfigField(Enum):
        SERVER_NAME = "server_name"
        DB_PATH = IMCPServer.ConfigFields.DATA_PATH.value
        DB_NAME = "db_name"

    _prefixes = [
        "Alpha", "Beta", "Gamma", "Delta", "Neo", "Future", "Quantum", "Sky", "Solar", "Eco",
        "Hyper", "Advanced", "NextGen", "Omega", "Vertex", "Cyber", "Aero", "Nano", "Digital", "Astro",
        "Infra", "Ultra", "Meta", "Xeno", "Fusion", "Titan", "Velocity", "Omni", "Synergy", "Evolution"
    ]

    _suffixes = [
        "Tech", "Corp", "Enterprises", "Solutions", "Group", "Holdings", "Systems", "Industries",
        "Networks", "Dynamics", "Technologies", "Global", "Analytics", "Capital", "Innovations",
        "Logistics", "Consulting", "Security", "Markets", "Energy", "Investments", "Biotech", "Aerospace", "Pharma"
    ]

    _tickers = get_instr_tickers()

    @staticmethod
    def get_tickers() -> List[Tuple[str, str, str]]:
        return InstrumentService._tickers

    def __init__(self,
                 logger: logging.Logger,
                 json_config: Dict[str, Any]) -> None:
        self._log: logging.Logger = logger
        self._config: Dict[str, Any] = json_config

        self._base_name = json_config.get(
            InstrumentService.ConfigField.DB_NAME.value, "InstrumentService")
        self._server_name: str = f"{self._base_name}{str(uuid.uuid4()).upper()}"

        self._staticDataService: StaticDataService = StaticDataService(
            logger, json_config)
        self._currencies: List[str] = self._staticDataService.get_all_currencies()[
            StaticDataService.StaticField.CURRENCY.value]
        self._industries: List[str] = self._staticDataService.get_all_industries()[
            StaticDataService.StaticField.INDUSTRY.value]
        self._venues: List[Tuple[str, str]] = self._staticDataService.get_all_venue_codes()[
            StaticDataService.StaticField.VENUE.value]

        self._db_path: str = json_config.get(
            InstrumentService.ConfigField.DB_PATH.value, "./")
        if not os.path.exists(self._db_path):
            raise self.ErrorLoadingInstrumentDatabase(
                f"Database path {self._db_path} does not exist.")

        self._db_name: str = json_config.get(
            InstrumentService.ConfigField.DB_NAME.value, "instrument.json")
        if not self._db_name:
            raise self.ErrorLoadingInstrumentDatabase(
                "Database name is not specified in the configuration.")

        # Generating is really only a one off to boostrap the database.
        gen_random: bool = False
        self._full_db_path = os.path.join(self._db_path, self._db_name)
        if not os.path.exists(self._full_db_path):
            if not gen_random:
                raise self.ErrorLoadingInstrumentDatabase(
                    f"Instrument database file {self._full_db_path} does not exist.")
            else:
                self._log.info(
                    f"Instrument database file {self._full_db_path} does not exist, generating random instruments.")
                self._generate_random_instruments(self._full_db_path)

        self._log.info(
            f"InstrumentService initialized name: {self._server_name} db: {self._full_db_path}")

        self._instument_db: List[Dict[str, Any]
                                 ] = self._load_instrument_database()
        if not self._instument_db:
            raise self.ErrorLoadingInstrumentDatabase(
                "Instrument database is empty or could not be loaded.")

    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def supported_tools(self) -> List[Tuple[str, Callable]]:
        return [("get_all_instrument_field_names", self.get_all_instrument_field_names),
                ("get_instruments", self.get_instruments)
                ]

    @property
    def supported_resources(self) -> List[Tuple[str, Callable]]:
        return []

    @property
    def supported_prompts(self) -> List[Tuple[str, Callable]]:
        return []

    def _random_company_name(self) -> str:
        return f"{random.choice(self._prefixes)} {random.choice(self._suffixes)}"

    def _random_ticker(self) -> str:
        return ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=random.randint(2, 4)))

    def _random_sedol(self) -> str:
        return f"B{random.randint(10, 99)}{random.randint(100, 999)}XYZ"

    def _random_isin(self) -> str:
        return f"{random.choice(['US', 'GB', 'JP', 'DE', 'AU', 'HK', 'CA', 'CN'])}00000{random.randint(1000, 9999)}2345"

    def _generate_random_instruments(self,
                                     full_db_path_and_filename: str) -> None:
        self._log.info(
            f"Generating random instruments and saving to {full_db_path_and_filename}")

        instruments: List[Dict[str, Any]] = []
        for _ in range(100):
            instruments.append({
                self.InstrumentField.GUID.value: str(uuid.uuid4()),
                self.InstrumentField.INSTRUMENT_LONG_NAME.value: self._random_company_name(),
                self.InstrumentField.REUTERS_CODE.value: f"{self._random_ticker()}.{random.choice(['L', 'N', 'K', 'F', 'AX', 'HK', 'TO'])}",
                self.InstrumentField.SEDOL.value: self._random_sedol(),
                self.InstrumentField.ISIN.value: self._random_isin(),
                self.InstrumentField.PRODUCT_TYPE.value: random.choice(["EQ", "DR"]),
                self.InstrumentField.INDUSTRY.value: random.choice(self._industries),
                self.InstrumentField.CURRENCY.value: random.choice(self._currencies),
                self.InstrumentField.LISTING_DATE.value: f"{random.randint(1980, 2024)}-{random.randint(1, 12):02}-{random.randint(1, 28):02}"
            })

        # Save to JSON file
        with open(full_db_path_and_filename, "w") as file:
            json.dump(instruments, file, indent=4)

        return

    def handle_request(self, request):
        # Implement this method as required by IMCPServer
        raise NotImplementedError("handle_request must be implemented.")

    def _load_instrument_database(self) -> List[Dict[str, Any]]:
        try:
            with open(self._full_db_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    raise self.ErrorLoadingInstrumentDatabase(
                        "Instrument database file is empty.")
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    raise self.ErrorLoadingInstrumentDatabase(
                        "Malformed JSON in instrument database.") from e
                return data
        except Exception as e:
            raise self.ErrorLoadingInstrumentDatabase(
                f"Error loading instrument database: {str(e)}") from e

    def get_all_instrument_field_names(self) -> Dict[str, Any]:
        try:
            return {"instrument_fields": [field.value for field in self.InstrumentField.__members__.values()]}
        except Exception as e:
            msg = f"Error retrieving instrument field names: {str(e)}"
            self._log.error(msg)
            return json.loads(json.dumps({"error": msg}))

    def _is_valid_field_name(self, field_name: str) -> bool:
        try:
            return field_name in [field.value for field in self.InstrumentField.__members__.values()]
        except Exception as e:
            self._log.error(
                f"Error validating field name '{field_name}': {str(e)}")
            return False

    def get_instruments(self,
                        field_name: Annotated[str, Field(description="The instrument field name to search for")],
                        regular_expression: Annotated[str, Field(description="Pattern to match field name against")]) -> Dict[str, Any]:
        try:
            # If the regular expression is a single '*', treat it as '.*'
            if regular_expression == "*":
                regex = ".*"
            if not self._is_valid_field_name(field_name):
                raise ValueError(
                    f"Instrument field name: [{field_name}] is not a recognized field name.")
            regex = re.compile(regular_expression)
            return {"instruments": [entry for entry in self._instument_db if field_name in entry and regex.search(entry[field_name])]}
        except Exception as e:
            msg = f"Error searching for instruments with key field [{field_name}] and matching expression [{regular_expression}]: {str(e)}"
            self._log.error(msg)
            return json.loads(json.dumps({"error": msg}))


if __name__ == "__main__":

    if (True):
        with open('/mcp/python/src/server/instrument_service/instrument.json') as f:
            data = json.load(f)

            tickers = []
        for instrument in data:
            if "Reuters_Code" in instrument:
                tickers.append(("Reuters_Code", instrument["Reuters_Code"]))
            if "SEDOL" in instrument:
                tickers.append(("SEDOL", instrument["SEDOL"]))
            if "ISIN" in instrument:
                tickers.append(("ISIN", instrument["ISIN"]))

    print(tickers)

    # Example usage
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("InstrumentServiceExample")

    config = {}
    config[InstrumentService.ConfigField.DB_NAME.value] = "instrument.json"
    config[InstrumentService.ConfigField.DB_PATH.value] = "python/src/server/instrument_service"
    config[InstrumentService.ConfigField.SERVER_NAME.value] = "InstrumentService"

    try:
        service = InstrumentService(logger,
                                    config)

        print(service.get_instruments(
            InstrumentService.InstrumentField.INSTRUMENT_LONG_NAME.value, r"^Alpha.*"))

    except InstrumentService.ErrorLoadingInstrumentDatabase as e:
        logger.error(f"Failed to load instrument database: {str(e)}")
