import logging
import uuid
import random
from typing import Dict, Any, Callable, List, Tuple, Annotated
from enum import Enum
from pydantic import Field
from i_mcp_server import IMCPServer
from .fx import FxConverter


class StaticDataService(IMCPServer):

    class StaticField(Enum):
        PRODUCT_TYPE = "Product_Type"
        INDUSTRY = "Industry"
        CURRENCY = "Currency"
        VENUE = "Venue"
        VENUE_DESCRIPTION = "Venue_Description"
        BROKER_CODE = "Broker_Code"
        BROKER_NAME = "Broker_Name"
        PRODUCT_CODE = "Product_Code"
        PRODUCT_TYPE_DESCRIPTION = "Product_Type_Description"
        ERROR = "Error"

    class ConfigField(Enum):
        SERVER_NAME = "server_name"
        DB_PATH = "db_path"
        DB_NAME = "db_name"

    _industries: List[str] = [
        "Technology", "Energy", "Healthcare", "Semiconductors", "Renewable Energy",
        "Financial Services", "Mining", "Automotive", "Retail", "Telecommunications",
        "Pharmaceuticals", "Entertainment", "Aerospace", "Biotechnology", "Agriculture"
    ]

    _products: List[Tuple[str, str]] = [
        ("EQ", "Cash Equity"),
        ("DR", "Depositary Receipt"),
    ]

    _brokers: List[Tuple[str, str]] = [
        ("BKRX1029AA", "Cascade Ridge Capital"),
        ("ZFTR8821LP", "Orion Summit Markets"),
        ("MLQW7265RC", "ArborPoint Financial"),
        ("G8YZ0013DV", "Vanguardon Trading Co."),
        ("XTPL4532HK", "Ironwave Global Brokers"),
        ("JREX9082BM", "Silverstrand Securities"),
        ("QWNE1206TK", "Evermist Holdings Ltd."),
        ("HFUL3479NZ", "Zephyr Rock Investments"),
        ("DMKO6314XY", "Bluecore Trading Group"),
        ("PNVG7763JU", "Elmspire Institutional")
    ]

    _venues: List[Tuple[str, str]] = [
        ("XNYS", "New York Stock Exchange"),
        ("XNAS", "NASDAQ"),
        ("XLON", "London Stock Exchange"),
        ("XJPX", "Tokyo Stock Exchange"),
        ("XPAR", "Euronext Paris"),
        ("XETR", "Frankfurt Stock Exchange"),
        ("XHKG", "Hong Kong Stock Exchange"),
        ("XASX", "Australian Securities Exchange"),
        ("XTSE", "Toronto Stock Exchange"),
        ("XSHG", "Shanghai Stock Exchange"),
        ("XSHE", "Shenzhen Stock Exchange"),
        ("BATE", "BATS Europe"),
        ("XCBF", "Cboe Global Markets"),
        ("XSES", "Singapore Exchange"),
        ("XFRA", "Deutsche Börse AG")
    ]

    _currencies: List[str] = ["USD", "GBP",
                              "JPY", "EUR", "AUD", "HKD", "CAD", "CNY"]

    def __init__(self,
                 logger: logging.Logger,
                 json_config: Dict[str, Any]) -> None:
        self._log: logging.Logger = logger
        self._config: Dict[str, Any] = json_config

        self._base_name = json_config.get(
            StaticDataService.ConfigField.DB_NAME.value, "StaticDataService")
        self._server_name: str = f"{self._base_name}{str(uuid.uuid4()).upper()}"
        self._fx_converter: FxConverter = FxConverter()

    def get_all_currencies(self) -> Dict[str, Any]:
        return {self.StaticField.CURRENCY.value: self._currencies.copy()}

    def get_all_venue_codes(self) -> Dict[str, Any]:
        venue_codes = [code for code, _ in self._venues]
        return {self.StaticField.VENUE.value: venue_codes}

    def get_venue_description(self,
                              code: Annotated[str, Field(description="The venue code to get the venue description of")]) -> Dict[str, str]:
        for c, desc in self._venues:
            if c == code:
                return {self.StaticField.VENUE_DESCRIPTION.value: desc}
        return {self.StaticField.ERROR.value: f"No such [{code}] venue"}

    def get_all_industries(self) -> Dict[str, List[str]]:
        return {self.StaticField.INDUSTRY.value: self._industries.copy()}

    def get_all_broker_codes(self) -> Dict[str, List[str]]:
        return {self.StaticField.BROKER_CODE.value: [code for code, _ in self._brokers]}

    def get_broker_name(self,
                        code: Annotated[str, Field(description="The broker code to get the broker description of")]) -> Dict[str, str]:
        for broker_code, name in self._brokers:
            if broker_code == code:
                return {self.StaticField.BROKER_NAME.value: name}
        return {self.StaticField.ERROR.value: f"No such broker [{code}]"}

    def get_all_product_type_codes(self) -> Dict[str, List[str]]:
        return {self.StaticField.PRODUCT_CODE.value: [code for code, _ in self._products]}

    def get_product_type_description(self,
                                     code: Annotated[str, Field(description="The product type code to get the product description of")]) -> Dict[str, str]:
        for product_code, desc in self._products:
            if product_code == code:
                return {self.StaticField.PRODUCT_TYPE_DESCRIPTION.value: desc}
        return {self.StaticField.ERROR.value: f"No such product [{code}]"}

    def get_fx_rate(self,
                    from_currency: Annotated[str, Field(description="The currency code to convert from (e.g., 'USD')")],
                    to_currency: Annotated[str, Field(description="The currency code to convert to (e.g., 'EUR')")]) -> Dict[str, Any]:
        try:
            rate = self._fx_converter.get_rate(from_currency, to_currency)
            if rate is not None:
                return {"rate": {"from_currency": from_currency,
                                 "to_currency": to_currency,
                                 "value": rate}}
            else:
                return {self.StaticField.ERROR.value: f"Conversion from {from_currency} to {to_currency} not possible, check for supported currencies."}
        except Exception as e:
            return {self.StaticField.ERROR.value: f"Error getting FX rate - from {from_currency} to {to_currency}: {str(e)}"}

    def _raise_not_implemented(self, method_name: str) -> None:
        raise NotImplementedError(
            f"StaticDataService method [{method_name}] must be implemented in a subclass."
        )

    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def supported_tools(self) -> List[Tuple[str, Callable]]:
        return [("get_all_currencies", self.get_all_currencies),
                ("get_all_industries", self.get_all_industries),
                ("get_all_product_type_codes", self.get_all_product_type_codes),
                ("get_all_broker_codes", self.get_all_broker_codes),
                ("get_all_venue_codes", self.get_all_venue_codes),
                ("get_venue_description", self.get_venue_description),
                ("get_broker_name", self.get_broker_name),
                ("get_product_type_description", self.get_product_type_description),
                ("get_fx_rate", self.get_fx_rate)
                ]

    @property
    def supported_resources(self) -> List[Tuple[str, Callable]]:
        return []

    @property
    def supported_prompts(self) -> List[Tuple[str, Callable]]:
        return []


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("StaticDataServiceExample")

    config = {}
    config[StaticDataService.ConfigField.SERVER_NAME.value] = "StaticDataService"

    try:
        service = StaticDataService(logger,
                                    config)

        currencies = service.get_all_currencies()
        logger.info(f"Available currencies: {currencies}")
        industries = service.get_all_industries()
        logger.info(f"Available industries: {industries}")
        broker_codes = service.get_all_broker_codes()
        logger.info(f"Available broker codes: {broker_codes}")
        venue_codes = service.get_all_venue_codes()
        logger.info(f"Available venue codes: {venue_codes}")
        product_types = service.get_all_product_type_codes()
        logger.info(f"Available product types: {product_types}")
        print(service.get_broker_name(random.choice(
            broker_codes[StaticDataService.StaticField.BROKER_CODE.value])))
        print(service.get_venue_description(random.choice(
            venue_codes[StaticDataService.StaticField.VENUE.value])))
        print(service.get_product_type_description(random.choice(
            product_types[StaticDataService.StaticField.PRODUCT_CODE.value])))

    except Exception as e:
        logger.error(f"Failed to initialise static database service: {e}")
