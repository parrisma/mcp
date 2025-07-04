import datetime
from http import client
import logging
import re
from re import A
from typing import Dict, Any, Callable, List, Tuple, Annotated
from flask.debughelpers import DebugFilesKeyError
from pydantic import Field
from i_mcp_server import IMCPServer
from enum import Enum
import uuid
import json
import os
import random
from static_data_service.static_data_service import StaticDataService
from static_data_service.permissions import Permissions
from client_service import ClientService
from instrument_service import tickers
from .staff import Staff
from .desks import Desks
from .algo_strategies import AlgoStrategies
from brokers import Brokers


class TradeService(IMCPServer):

    class ErrorLoadingTradeDatabase(RuntimeError):
        pass

    class TradeFields(Enum):
        TRADE_ID = "trade_id"
        ORDER_ID = "order_id"
        INSTRUMENT_TICKER = "instrument.ticker"
        INSTRUMENT_ISIN = "instrument.isin"
        SIDE = "side"
        ORDER_TYPE = "order_type"
        QUANTITY_ORDERED = "quantity.ordered"
        QUANTITY_EXECUTED = "quantity.executed"
        PRICE_LIMIT = "price.limit"
        PRICE_EXECUTED = "price.executed"
        TIMESTAMPS_ORDER_PLACED = "timestamps.order_placed"
        TIMESTAMPS_EXECUTED = "timestamps.executed"
        EXECUTION_VENUE = "execution_venue"
        ORDER_STATUS = "order_status"
        COUNTERPARTY_CLIENT_ID = "counterparty.client_id"
        COUNTERPARTY_ACCOUNT_NUMBER = "counterparty.account_number"
        COUNTERPARTY_BROKER = "counterparty.broker"
        COUNTERPARTY_TRADER_ID = "counterparty.trader_id"
        SETTLEMENT_DATE = "settlement.settlement_date"
        SETTLEMENT_INSTRUCTIONS = "settlement.instructions"
        REGULATORY_MIFID_II_ALGO_TRADE = "regulatory.mifid_ii.algo_trade"
        REGULATORY_MIFID_II_SHORT_SELL = "regulatory.mifid_ii.short_sell"
        REGULATORY_MIFID_II_EXECUTION_DECISION_MAKER = "regulatory.mifid_ii.execution_decision_maker"
        REGULATORY_MIFID_II_INVESTMENT_DECISION_MAKER = "regulatory.mifid_ii.investment_decision_maker"
        REGULATORY_REPORTING_FLAGS = "regulatory.reporting_flags"
        AUDIT_VERSION = "audit.version"
        AUDIT_CHANGE_LOG = "audit.change_log"
        FEES_COMMISSION = "fees.commission"
        FEES_EXCHANGE_FEE = "fees.exchange_fee"
        FEES_TOTAL = "fees.total"
        FEES_CURRENCY = "fees.currency"
        ANALYTICS_ALGO_TYPE = "analytics.algo_type"
        ANALYTICS_VWAP = "analytics.vwap"
        ANALYTICS_VOLUME_PARTICIPATION = "analytics.volume_participation"

    _algo_strategies = AlgoStrategies()

    _brokers: Brokers = Brokers()

    _staff = Staff()

    _desks = Desks()

    _permissions = Permissions()

    _sides = ["Buy", "Sell"]

    _order_types = ["Market", "Limit", "Stop"]

    _tickers = tickers.get_instr_tickers()

    _client_ids = ClientService.get_client_ids()

    _trading_account_ids = ClientService.get_trading_account_ids()

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
            TradeService.ConfigField.DB_NAME.value, "TradeService")
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
            TradeService.ConfigField.DB_PATH.value, "./")
        if not os.path.exists(self._db_path):
            raise self.ErrorLoadingTradeDatabase(
                f"Database path {self._db_path} does not exist.")

        self._db_name: str = json_config.get(
            TradeService.ConfigField.DB_NAME.value, "trades.json")
        if not self._db_name:
            raise self.ErrorLoadingTradeDatabase(
                "Database name is not specified in the configuration.")

        self._full_db_path = os.path.join(self._db_path, self._db_name)
        if not os.path.exists(self._full_db_path):
            self.generate_trades(self._full_db_path)

        self._log.info(
            f"TradeService initialized name: {self._server_name} db: {self._full_db_path}")

        self._instument_db: List[Dict[str, Any]
                                 ] = self._load_trade_database()
        if not self._instument_db:
            raise self.ErrorLoadingTradeDatabase(
                "Trade database is empty or could not be loaded.")

    def choose_algo_analytics(self,
                              executed_price: float) -> Dict[str, Any]:
        algos = {
            "VWAP": lambda: {
                "algo_type": "VWAP",
                "vwap": round(executed_price + random.uniform(-0.2, 0.2), 2),
                "volume_participation": f"{random.randint(5, 30)}%"
            },
            "TWAP": lambda: {
                "algo_type": "TWAP",
                "twap": round(executed_price + random.uniform(-0.2, 0.2), 2),
                "interval_seconds": random.choice([60, 300, 900])
            },
            "ARRV": lambda: {
                "algo_type": "Arrival Price",
                "arrival_price": round(executed_price + random.uniform(-0.3, 0.3), 2),
                "implementation_shortfall": round(random.uniform(0.01, 0.5), 2)
            },
            "POVL": lambda: {
                "algo_type": "Percentage of Volume",
                "target_participation": f"{random.randint(10, 50)}%",
                "realized_participation": f"{random.randint(8, 52)}%"
            },
            "SNPR": lambda: {
                "algo_type": "Sniper",
                "latency_ms": random.randint(2, 10),
                "hit_rate": f"{random.randint(90, 99)}%",
                "trigger_spread": round(random.uniform(0.01, 0.05), 4)
            },
            "ICBG": lambda: {
                "algo_type": "Iceberg",
                "display_quantity": random.randint(100, 1000),
                "reserve_quantity": random.randint(1000, 10000)
            }
        }

        selected_algo = random.choice(list(algos.keys()))
        return algos[selected_algo]()

    def generate_random_trade(self):

        ticker, isin, _ = random.choice(self._tickers)
        side = random.choice(self._sides)
        order_type = random.choice(self._order_types)
        quantity = random.randint(100, 9000000)
        limit_price = round(random.uniform(10, 1000), 2)
        executed_price = round(limit_price + random.uniform(-0.5, 0.5), 2)
        order_time = datetime.datetime.now(
        ) - datetime.timedelta(minutes=random.randint(1, 300))
        execution_time = order_time + \
            datetime.timedelta(seconds=random.randint(5, 60))
        client_id = random.choice(self._client_ids)
        account_number = random.choice(self._trading_account_ids)
        trader = (random.choice(self._staff.get_all_trader_data()))[0]
        desk_1 = random.choice(self._desks.get_all_desks())
        desk_2 = random.choice(self._desks.get_all_desks())

        return {
            "trade_id": f"TRD_{str(uuid.uuid4())}",
            "order_id": f"ORD_{str(uuid.uuid4())}",
            "instrument": {
                "ticker": ticker,
                "isin": isin
            },
            "side": side,
            "order_type": order_type,
            "quantity": {
                "ordered": quantity,
                "executed": quantity
            },
            "price": {
                "limit": limit_price,
                "executed": executed_price
            },
            "timestamps": {
                "order_placed": order_time.isoformat(),
                "executed": execution_time.isoformat()
            },
            "execution_venue": random.choice(self._venues),
            "order_status": "Filled",
            "counterparty": {
                "client_id": client_id,
                "account_number": account_number,
                "broker": random.choice(self._brokers.get_all_brokers()),
                "trader_id": trader
            },
            "settlement": {
                "settlement_date": (execution_time + datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
                "instructions": "DvP"
            },
            "regulatory": {
                "mifid_ii": {
                    "algo_trade": random.choice([True, False]),
                    "short_sell": random.choice([True, False]),
                    "execution_decision_maker": desk_1,
                    "investment_decision_maker": desk_2
                },
                "reporting_flags": ["On-Venue"]
            },
            "audit": {
                "version": "1.0",
                "change_log": [
                    {"timestamp": order_time.isoformat(), "action": "order_placed"},
                    {"timestamp": execution_time.isoformat(), "action": "executed"}
                ]
            },
            "fees": {
                "commission": round(quantity * 0.001, 2),
                "exchange_fee": round(quantity * 0.0002, 2),
                "total": round(quantity * 0.0012, 2),
                "currency": random.choice(self._currencies)
            },
            "analytics": self.choose_algo_analytics(executed_price)
        }

    def generate_trades(self,
                        full_db_path_and_filename: str,
                        n=200) -> None:
        self._log.info(
            f"Generating random trades and saving to {full_db_path_and_filename}")

        trades = [self.generate_random_trade() for i in range(n)]

        # Save to JSON file
        with open(full_db_path_and_filename, "w") as file:
            json.dump(trades, file, indent=4)

        return

    def _load_trade_database(self) -> List[Dict[str, Any]]:
        try:
            with open(self._full_db_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    raise self.ErrorLoadingTradeDatabase(
                        "Trade database file is empty.")
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    raise self.ErrorLoadingTradeDatabase(
                        "Malformed JSON in trade database.") from e
                return data
        except Exception as e:
            raise self.ErrorLoadingTradeDatabase(
                f"Error loading trade database: {str(e)}") from e

    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def supported_tools(self) -> List[Tuple[str, Callable]]:
        return [
            ("get_all_algo_types", self.get_all_algo_types),
            ("get_algo_description", self.get_algo_description),
            ("get_all_brokers", self.get_all_brokers),
            ("get_broker_description", self.get_broker_description),
            ("get_all_traders", self.get_all_traders),
            ("get_trader_description", self.get_trader_description),
            ("get_all_desks", self.get_all_desks),
            ("get_desk_description", self.get_desk_description),
            ("get_all_staff_types", self.get_all_staff_types),
            ("get_staff_by_type", self.get_staff_by_type),
            ("get_staff_type_description", self.get_staff_type_description),
            ("get_desks_staff_has_access_to", self.get_desks_staff_has_access_to),
            ("get_staff_who_have_access_to_desk",
             self.get_staff_who_have_access_to_desk),
            ("does_staff_id_have_desk_access", self.does_staff_id_have_desk_access),
            ("get_permissions", self.get_permissions),
            ("get_all_trade_field_names", self.get_all_trade_field_names),
            ("get_all_sides", self.get_all_sides),
            ("get_all_order_types", self.get_all_order_types),
            ("get_all_client_ids", self.get_all_client_ids),
            ("get_all_trading_account_ids", self.get_all_trading_account_ids),
            ("get_trades", self.get_trades)
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

    def get_all_algo_types(self) -> Dict[str, Any]:
        algo_types = self._algo_strategies.get_all_algo_types()
        return {"algo_types": algo_types}

    def get_algo_description(self,
                             code: Annotated[str, Field(description="The algo type code to get the description of")]) -> Dict[str, str]:
        description = self._algo_strategies.get_algo_description(code)
        if description:
            return {"algo_description": description}
        return json.loads(json.dumps({"error": f"No such [{code}] algo type"}))

    def get_all_brokers(self) -> Dict[str, Any]:
        brokers = [code for code, _ in self._brokers.get_all_brokers()]
        return {"brokers": brokers}

    def get_broker_description(self,
                               code: Annotated[str, Field(description="The broker code to get the description of")]) -> Dict[str, str]:
        for c, desc in self._brokers.get_all_brokers():
            if c == code:
                return {"broker_description": desc}
        return json.loads(json.dumps({"error": f"No such [{code}] broker"}))

    def get_all_traders(self) -> Dict[str, Any]:
        traders = self._staff.get_all_traders()
        return {"traders": traders}

    def get_trader_description(self,
                               code: Annotated[str, Field(description="The trader code to get the description of")]) -> Dict[str, str]:
        description = self._staff.get_trader_description(code)
        if description:
            return {"trader_description": description}
        return json.loads(json.dumps({"error": f"No such [{code}] trader"}))

    def get_all_desks(self) -> Dict[str, Any]:
        desks = self._desks.get_all_desks()
        return {"desks": desks}

    def get_desk_description(self,
                             code: Annotated[str, Field(description="The desk code to get the description of")]) -> Dict[str, str]:
        description = self._desks.get_desk_description(code)
        if description:
            return {"desk_description": description}
        return json.loads(json.dumps({"error": f"No such [{code}] desk"}))

    def get_all_staff_types(self) -> Dict[str, Any]:
        staff_types_with_descriptions = Staff.get_all_staff_types_with_descriptions()
        staff_types = [code for code, _ in staff_types_with_descriptions]
        return {"staff_types": staff_types}

    def get_staff_by_type(self,
                          staff_type: Annotated[str, Field(description="The staff type code to get staff members for")]) -> Dict[str, Any]:
        staff_members = Staff.get_staff_by_type(staff_type)
        return {"staff_members": staff_members}

    def get_staff_type_description(self,
                                   staff_code: Annotated[str, Field(description="The three character staff type code to get the description for")]) -> Dict[str, str]:
        description = Staff.get_staff_type_description(staff_code)
        if description:
            return {"staff_type_description": description}
        return json.loads(json.dumps({"error": f"Staff type '{staff_code}' does not exist"}))

    def get_desks_staff_has_access_to(self,
                                      staff_id: Annotated[str, Field(description="The staff ID (e.g., 'TRD_HK_001') to get desk access permissions for")]) -> Dict[str, Any]:
        """Get all trading desks that a specific staff member has access to view data for."""
        try:
            desks = Staff.get_desks_staff_has_access_to(staff_id)
            if desks:
                return {"staff_id": staff_id, "accessible_desks": desks}
            else:
                return {"staff_id": staff_id, "accessible_desks": [], "message": f"Staff member '{staff_id}' has no desk access or does not exist"}
        except Exception as e:
            msg = f"Error retrieving desk access for staff '{staff_id}': {str(e)}"
            self._log.error(msg)
            return json.loads(json.dumps({"error": msg}))

    def get_staff_who_have_access_to_desk(self,
                                          desk_code: Annotated[str, Field(description="The desk code (e.g., 'Desk001') to get staff access list for")]) -> Dict[str, Any]:
        """Get all staff members who have access to view data for a specific trading desk."""
        try:
            staff_list = Staff.get_staff_who_have_access_to_desk(desk_code)
            if staff_list:
                return {"desk_code": desk_code, "authorized_staff": staff_list}
            else:
                return {"desk_code": desk_code, "authorized_staff": [], "message": f"No staff have access to desk '{desk_code}' or desk does not exist"}
        except Exception as e:
            msg = f"Error retrieving staff access for desk '{desk_code}': {str(e)}"
            self._log.error(msg)
            return json.loads(json.dumps({"error": msg}))

    def does_staff_id_have_desk_access(self,
                                       staff_id: Annotated[str, Field(description="The staff ID (e.g., 'TRD_HK_001') to check access for")],
                                       desk_code: Annotated[str, Field(description="The desk code (e.g., 'Desk001') to check access to")]) -> Dict[str, Any]:
        """Check if a specific staff member has access to view data for a specific trading desk."""
        try:
            has_access = Staff.does_staff_id_have_desk_access(
                staff_id, desk_code)
            return {
                "staff_id": staff_id,
                "desk_code": desk_code,
                "has_access": has_access,
                "message": f"Staff '{staff_id}' {'has' if has_access else 'does not have'} access to desk '{desk_code}'"
            }
        except Exception as e:
            msg = f"Error checking access for staff '{staff_id}' to desk '{desk_code}': {str(e)}"
            self._log.error(msg)
            return json.loads(json.dumps({"error": msg}))

    def get_permissions(self,
                        role: Annotated[str, Field(description="The user role name (e.g., 'Sales Trader', 'Execution Trader', 'Operations', 'Finance', 'Technology', 'Compliance', 'Research') to get permissions for")]) -> Dict[str, Any]:
        """Get the permissions for a specific user role, showing what capabilities they have read/write access to."""
        try:
            permissions = self._permissions.get_permissions(role)
            return {
                "role": role,
                "permissions": permissions
            }
        except ValueError as e:
            return json.loads(json.dumps({"error": str(e)}))
        except Exception as e:
            msg = f"Error retrieving permissions for role '{role}': {str(e)}"
            self._log.error(msg)
            return json.loads(json.dumps({"error": msg}))

    def get_all_trade_field_names(self) -> Dict[str, Any]:
        try:
            return {"trade_fields": [field.value for field in self.TradeFields.__members__.values()]}
        except Exception as e:
            msg = f"Error retrieving trade field names: {str(e)}"
            self._log.error(msg)
            return json.loads(json.dumps({"error": msg}))

    def get_all_sides(self) -> Dict[str, Any]:
        return {"sides": list(self._sides)}

    def get_all_order_types(self) -> Dict[str, Any]:
        return {"order_types": list(self._order_types)}

    def get_all_client_ids(self) -> Dict[str, Any]:
        return {"client_ids": list(self._client_ids)}

    def get_all_trading_account_ids(self) -> Dict[str, Any]:
        return {"trading_account_ids": list(self._trading_account_ids)}

    def _get_nested_value(self, data: Dict[str, Any], keys: List[str]) -> Any:
        """Safely retrieves a nested value from a dictionary."""
        current_value = data
        for key in keys:
            if isinstance(current_value, dict) and key in current_value:
                current_value = current_value[key]
            else:
                return None  # Key not found or not a dictionary at this level
        return current_value

    def get_trades(self,
                   field_name: Annotated[str, Field(description="The trade field name to search for")],
                   regular_expression: Annotated[str, Field(description="Pattern to match field value against")]) -> Dict[str, Any]:
        try:
            # Verify field_name is defined by TradeFields Enum
            if field_name not in [field.value for field in self.TradeFields]:
                raise ValueError(
                    f"Field name '{field_name}' is not a defined trade field.")

            # If the regular expression is a single '*', treat it as '.*'
            if regular_expression == "*":
                regex = re.compile(".*")
            else:
                regex = re.compile(regular_expression)

            # Split the field_name by '.' to handle nested fields
            keys = field_name.split('.')

            return {
                "trades": [
                    entry for entry in self._instument_db
                    if self._get_nested_value(entry, keys) is not None and regex.search(str(self._get_nested_value(entry, keys)))
                ]
            }
        except Exception as e:
            msg = f"Error searching for trades with key field [{field_name}] and matching expression [{regular_expression}]: {str(e)}"
            self._log.error(msg)
            return json.loads(json.dumps({"error": msg}))



if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("TradeServiceExample")

    config = {}
    config[TradeService.ConfigField.DB_NAME.value] = "trades.json"
    config[TradeService.ConfigField.DB_PATH.value] = "python/src/server/trade_service"
    config[TradeService.ConfigField.SERVER_NAME.value] = "TradeService"

    try:
        service = TradeService(logger,
                               config)

        print(service.get_all_trade_field_names())
        print(service.get_all_algo_types())
        print(service.get_algo_description("VWAP"))
        print(service.get_all_brokers())
        print(service.get_broker_description("BKRX1029AA"))
        print(service.get_all_traders())
        print(service.get_trader_description("TRD_HK_001"))
        print(service.get_all_desks())
        print(service.get_desk_description("Desk001"))
        print(service.get_all_sides())
        print(service.get_all_order_types())
        print(service.get_all_client_ids())
        print(service.get_all_trading_account_ids())
        print(service.get_trades(
            TradeService.TradeFields.ANALYTICS_ALGO_TYPE.value, "VWAP"))
        print(service.get_trades("", "Bob Smith"))

    except TradeService.ErrorLoadingTradeDatabase as e:
        logger.error(f"Failed to load trades database: {str(e)}")
