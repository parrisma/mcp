import datetime
import logging
import re
from re import A
from typing import Dict, Any, Callable, List, Tuple, Annotated
from pydantic import Field
from i_mcp_server import IMCPServer
from enum import Enum
import uuid
import json
import os
import random


class TradeService(IMCPServer):

    class ErrorLoadingTradeDatabase(RuntimeError):
        pass

    class TradeField(Enum):
        TRADE_ID = "Trade_ID"
        ORDER_ID = "Order_ID"
        INSTRUMENT_TICKER = "Instrument_Ticker"
        INSTRUMENT_ISIN = "Instrument_ISIN"
        SIDE = "Side"
        ORDER_TYPE = "Order_Type"
        QUANTITY_ORDERED = "Quantity_Ordered"
        QUANTITY_EXECUTED = "Quantity_Executed"
        PRICE_LIMIT = "Price_Limit"
        PRICE_EXECUTED = "Price_Executed"
        TIMESTAMP_ORDER_PLACED = "Timestamp_Order_Placed"
        TIMESTAMP_EXECUTED = "Timestamp_Executed"
        EXECUTION_VENUE = "Execution_Venue"
        ORDER_STATUS = "Order_Status"
        CLIENT_ID = "Client_ID"
        ACCOUNT_NUMBER = "Account_Number"
        BROKER = "Broker"
        TRADER_ID = "Trader_ID"
        SETTLEMENT_DATE = "Settlement_Date"
        SETTLEMENT_INSTRUCTIONS = "Settlement_Instructions"
        MIFID_ALGO_TRADE = "MiFID_Algo_Trade"
        MIFID_SHORT_SELL = "MiFID_Short_Sell"
        MIFID_EXECUTION_DECISION_MAKER = "MiFID_Execution_Decision_Maker"
        MIFID_INVESTMENT_DECISION_MAKER = "MiFID_Investment_Decision_Maker"
        REPORTING_FLAGS = "Reporting_Flags"
        AUDIT_VERSION = "Audit_Version"
        AUDIT_CHANGE_LOG = "Audit_Change_Log"
        FEES_COMMISSION = "Fees_Commission"
        FEES_EXCHANGE = "Fees_Exchange"
        FEES_TOTAL = "Fees_Total"
        FEES_CURRENCY = "Fees_Currency"
        ANALYTICS_ARRIVAL_PRICE = "Analytics_Arrival_Price"
        ANALYTICS_VWAP = "Analytics_VWAP"
        ANALYTICS_SLIPPAGE = "Analytics_Slippage"

    algo_strategies: List[Tuple[str, str]] = [
        ("VWAP", "Volume Weighted Average Price - trades in proportion to historical volume"),
        ("TWAP", "Time Weighted Average Price - executes evenly over time"),
        ("ARRV", "Arrival Price - minimizes implementation shortfall"),
        ("POVL", "Percentage of Volume - trades as a % of real-time market volume"),
        ("CLSE", "Close - targets the closing auction"),
        ("OPCL", "Opportunistic Close - adapts to volume near market close"),
        ("SORR", "Smart Order Router - routes orders to best venues for execution"),
        ("LIQD", "Liquidity Seeking - aggressively searches for hidden liquidity"),
        ("DRKA", "Dark Aggregator - combines multiple dark pools for execution"),
        ("ALPH", "Alpha Seeking - uses predictive signals to optimize timing"),
        ("SNPR", "Sniper - waits passively, then quickly executes when liquidity appears"),
        ("ICBG", "Iceberg - shows small visible size, hides the rest"),
        ("TOPN", "Target Open - focuses execution around market open"),
        ("TCLS", "Target Close - focuses execution around market close"),
        ("VCUR", "Volume Curve - follows a predefined historical volume profile"),
        ("IMPL", "Implementation Shortfall - balances market impact and price risk")
    ]

    class ConfigField(Enum):
        SERVER_NAME = "server_name"
        DB_PATH = "db_path"
        DB_NAME = "db_name"

    _industries: List[str] = [
        "Technology", "Energy", "Healthcare", "Semiconductors", "Renewable Energy",
        "Financial Services", "Mining", "Automotive", "Retail", "Telecommunications",
        "Pharmaceuticals", "Entertainment", "Aerospace", "Biotechnology", "Agriculture"
    ]

    _markets: List[Tuple[str, str]] = [
        ("NYSE", "NYS"),
        ("London Stock Exchange", "LSE"),
        ("Tokyo Stock Exchange", "TSE"),
        ("Frankfurt Stock Exchange", "FSE"),
        ("Australian Securities Exchange", "ASX"),
        ("Hong Kong Stock Exchange", "HKG"),
        ("Toronto Stock Exchange", "TSX"),
        ("Shanghai Stock Exchange", "SSE"),
        ("Euronext", "EUX"),
        ("NASDAQ", "NSD")
    ]

    _currencies: List[str] = ["USD", "GBP",
                              "JPY", "EUR", "AUD", "HKD", "CAD", "CNY"]

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

    def __init__(self,
                 logger: logging.Logger,
                 json_config: Dict[str, Any]) -> None:
        self._log: logging.Logger = logger
        self._config: Dict[str, Any] = json_config

        self._base_name = json_config.get(
            TradeService.ConfigField.DB_NAME.value, "InstrumentService")
        self._server_name: str = f"{self._base_name}{str(uuid.uuid4()).upper()}"

        self._db_path: str = json_config.get(
            TradeService.ConfigField.DB_PATH.value, "./")
        if not os.path.exists(self._db_path):
            raise self.ErrorLoadingTradeDatabase(
                f"Database path {self._db_path} does not exist.")

        self._db_name: str = json_config.get(
            TradeService.ConfigField.DB_NAME.value, "instrument.json")
        if not self._db_name:
            raise self.ErrorLoadingTradeDatabase(
                "Database name is not specified in the configuration.")

        self._full_db_path = os.path.join(self._db_path, self._db_name)
        if not os.path.exists(self._full_db_path):
            self._generate_random_instruments(self._full_db_path)

        self._log.info(
            f"InstrumentService initialized name: {self._server_name} db: {self._full_db_path}")

        self._instument_db: List[Dict[str, Any]
                                 ] = self._load_instrument_database()
        if not self._instument_db:
            raise self.ErrorLoadingTradeDatabase(
                "Instrument database is empty or could not be loaded.")

        self._log.info(f"Current working directory: {os.getcwd()}")

    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def supported_tools(self) -> List[Tuple[str, Callable]]:
        return [("get_all_currencies", self.get_all_currencies),
                ("get_all_industries", self.get_all_insdutries),
                ("get_all_markets", self.get_all_markets),
                ("get_all_field_names", self.get_all_field_names),
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
                self.InstrumentField.MARKET.value: random.choice(self._markets)[0],
                self.InstrumentField.MARKET_ID.value: random.choice(self._markets)[1],
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
                    raise self.ErrorLoadingTradeDatabase(
                        "Instrument database file is empty.")
                try:
                    data = json.loads(content)
                except json.JSONDecodeError as e:
                    raise self.ErrorLoadingTradeDatabase(
                        "Malformed JSON in instrument database.") from e
                return data
        except Exception as e:
            raise self.ErrorLoadingTradeDatabase(
                f"Error loading instrument database: {e}") from e

    def get_all_markets(self) -> Dict[str, Any]:
        return {"markets": [{"market": name, "market_id": id} for name, id in self._markets]}

    def get_all_currencies(self) -> Dict[str, Any]:
        return {"industries": self._currencies}

    def get_all_insdutries(self) -> Dict[str, Any]:
        return {"industries": self._industries}

    def get_all_field_names(self) -> List[str]:
        return [field.value for field in self.InstrumentField.__members__.values()]

    def get_instruments(self,
                        field_name: Annotated[str, Field(description="The instrument field name to search for")],
                        regular_expression: Annotated[str, Field(description="Pattern to match field name against")]) -> List[Dict[str, Any]]:
        try:
            regex = re.compile(regular_expression)
            return [entry for entry in self._instument_db if field_name in entry and regex.search(entry[field_name])]
        except Exception as e:
            msg = f"Error searching for instruments with key field [{field_name}] and matching expression [{regular_expression}]: {e}"
            self._log.error(msg)
            return [{"error": msg}]


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("InstrumentServiceExample")

    config = {}
    config[TradeService.ConfigField.DB_NAME.value] = "instrument.json"
    config[TradeService.ConfigField.DB_PATH.value] = "python/src/server/instrument_service"
    config[TradeService.ConfigField.SERVER_NAME.value] = "InstrumentService"

    try:
        service = TradeService(logger,
                               config)

        print(service.get_instruments(
            TradeService.InstrumentField.INSTRUMENT_LONG_NAME.value, r"^Alpha.*"))

        print(service.get_all_markets())
        print(service.get_all_currencies())
        print(service.get_all_insdutries())

    except TradeService.ErrorLoadingTradeDatabase as e:
        logger.error(f"Failed to load instrument database: {e}")


def choose_algo_analytics(executed_price: float) -> dict:
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


def generate_random_trade(index=0):
    tickers = [
        ("AAPL", "US0378331005"), ("GOOGL",
                                   "US02079K3059"), ("MSFT", "US5949181045"),
        ("AMZN", "US0231351067"), ("TSLA", "US88160R1014")
    ]

    brokers: List[Tuple[str, str]] = [
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

    venues = ["XNAS", "XNYS", "BATE", "CHIX"]
    sides = ["Buy", "Sell"]
    order_types = ["Market", "Limit", "Stop"]
    currencies = ["USD", "GBP", "EUR"]

    ticker, isin = random.choice(tickers)
    side = random.choice(sides)
    order_type = random.choice(order_types)
    quantity = random.randint(100, 100000)
    limit_price = round(random.uniform(10, 1000), 2)
    executed_price = round(limit_price + random.uniform(-0.5, 0.5), 2)
    order_time = datetime.datetime.now(
    ) - datetime.timedelta(minutes=random.randint(1, 300))
    execution_time = order_time + \
        datetime.timedelta(seconds=random.randint(5, 60))

    return {
        "trade_id": f"TRD{datetime.datetime.now().strftime('%Y%m%d')}{index:04d}",
        "order_id": str(uuid.uuid4()),
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
        "execution_venue": random.choice(venues),
        "order_status": "Filled",
        "counterparty": {
            "client_id": f"CLT{random.randint(10000, 99999)}",
            "account_number": f"ACCT{random.randint(100000, 999999)}",
            "broker": random.choice(brokers),
            "trader_id": f"TRD{random.randint(100, 999)}"
        },
        "settlement": {
            "settlement_date": (execution_time + datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
            "instructions": "DvP"
        },
        "regulatory": {
            "mifid_ii": {
                "algo_trade": random.choice([True, False]),
                "short_sell": random.choice([True, False]),
                "execution_decision_maker": "Desk001",
                "investment_decision_maker": "Desk001"
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
            "currency": random.choice(currencies)
        },
        "analytics": choose_algo_analytics(executed_price)
    }


def generate_trades(n=10):
    return [generate_random_trade(i) for i in range(n)]


# Example usage
print(json.dumps(generate_trades(3), indent=2))
