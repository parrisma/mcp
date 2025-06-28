import logging
import uuid
import random
from typing import Dict, Any, Callable, List, Tuple, Annotated
from enum import Enum
from pydantic import Field
from i_mcp_server import IMCPServer
from .fx import FxConverter
from .permissions import Permissions
from .industries import Industries
from .products import Products
from .brokers import Brokers
from .venues import Venues
from .currencies import Currencies


class StaticDataService(IMCPServer):

    class StaticField(Enum):
        PRODUCT_TYPE = "Product_Type"
        INDUSTRY = "Industry"
        CURRENCY = "Currency"
        ROLES = "Roles"
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

    def __init__(self,
                 logger: logging.Logger,
                 json_config: Dict[str, Any]) -> None:
        self._log: logging.Logger = logger
        self._config: Dict[str, Any] = json_config

        self._base_name = json_config.get(
            StaticDataService.ConfigField.DB_NAME.value, "StaticDataService")
        self._server_name: str = f"{self._base_name}{str(uuid.uuid4()).upper()}"
        self._fx_converter: FxConverter = FxConverter()
        self._permissions: Permissions = Permissions()
        self._industries: Industries = Industries()
        self._products: Products = Products()
        self._brokers: Brokers = Brokers()
        self._venues: Venues = Venues()
        self._currencies: Currencies = Currencies()

    def get_all_roles(self) -> Dict[str, List[str]]:
        return {self.StaticField.ROLES.value: self._permissions.get_roles()}

    def get_all_currencies(self) -> Dict[str, Any]:
        return {self.StaticField.CURRENCY.value: self._currencies.get_all_currencies()}

    def get_all_venue_codes(self) -> Dict[str, Any]:
        venue_codes = self._venues.get_all_venue_codes()
        return {self.StaticField.VENUE.value: venue_codes}

    def get_venue_description(self,
                              code: Annotated[str, Field(description="The venue code to get the venue description of")]) -> Dict[str, str]:
        desc = self._venues.get_venue_description(code)
        if desc is not None:
            return {self.StaticField.VENUE_DESCRIPTION.value: desc}
        return {self.StaticField.ERROR.value: f"No such [{code}] venue"}

    def get_all_industries(self) -> Dict[str, List[str]]:
        return {self.StaticField.INDUSTRY.value: self._industries.get_all_industries()}

    def get_all_broker_codes(self) -> Dict[str, List[str]]:
        return {self.StaticField.BROKER_CODE.value: self._brokers.get_all_broker_codes()}

    def get_broker_name(self,
                        code: Annotated[str, Field(description="The broker code to get the broker description of")]) -> Dict[str, str]:
        name = self._brokers.get_broker_name(code)
        if name is not None:
            return {self.StaticField.BROKER_NAME.value: name}
        return {self.StaticField.ERROR.value: f"No such broker [{code}]"}

    def get_all_product_type_codes(self) -> Dict[str, List[str]]:
        return {self.StaticField.PRODUCT_CODE.value: self._products.get_all_product_type_codes()}

    def get_product_type_description(self,
                                     code: Annotated[str, Field(description="The product type code to get the product description of")]) -> Dict[str, str]:
        desc = self._products.get_product_type_description(code)
        if desc is not None:
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
        logger.error(f"Failed to initialise static database service: {str(e)}")
