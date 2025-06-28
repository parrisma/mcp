import json
import logging
import requests
import urllib.parse
from typing import Dict, Any, List
from trade_service import TradeService


class TradeVectorizer:
    """
    Utility class to vectorize trades by sending them to the Vector DB web interface.
    """

    def __init__(self,
                 trade_service: TradeService,
                 vector_db_host: str = "0.0.0.0",
                 vector_db_port: int = 6000):
        self.trade_service = trade_service
        self.vector_db_base_url = f"http://{vector_db_host}:{vector_db_port}"
        self.logger = logging.getLogger(__name__)

    def create_trade_summary(self, trade: Dict[str, Any]) -> str:
        """
        Create a human-readable summary of key trade details for vectorization.
        """
        try:
            # Extract key trade information
            trade_id = trade.get("trade_id", "Unknown")
            instrument = trade.get("instrument", {})
            ticker = instrument.get("ticker", "Unknown")
            isin = instrument.get("isin", "Unknown")
            side = trade.get("side", "Unknown")
            quantity = trade.get("quantity", {})
            ordered_qty = quantity.get("ordered", 0)
            executed_qty = quantity.get("executed", 0)
            price = trade.get("price", {})
            executed_price = price.get("executed", 0)
            counterparty = trade.get("counterparty", {})
            client_id = counterparty.get("client_id", "Unknown")
            trader_id = counterparty.get("trader_id", "Unknown")
            execution_venue = trade.get("execution_venue", "Unknown")
            order_status = trade.get("order_status", "Unknown")
            timestamps = trade.get("timestamps", {})
            executed_time = timestamps.get("executed", "Unknown")
            regulatory = trade.get("regulatory", {})
            mifid_ii = regulatory.get("mifid_ii", {})
            execution_decision_maker = mifid_ii.get(
                "execution_decision_maker", "Unknown")
            analytics = trade.get("analytics", {})
            algo_type = analytics.get("algo_type", "Unknown")

            # Create a comprehensive summary
            summary = f"""Trade {trade_id}: {side} {executed_qty:,} shares of {ticker} ({isin}) at ${executed_price:.2f} per share. 
Client: {client_id}, Trader: {trader_id}, Venue: {execution_venue}, Status: {order_status}. 
Executed: {executed_time}, Decision Maker: {execution_decision_maker}, Algorithm: {algo_type}. 
Total value: ${executed_qty * executed_price:,.2f}."""

            return summary

        except Exception as e:
            self.logger.error(
                f"Error creating trade summary for trade {trade.get('trade_id', 'Unknown')}: {str(e)}")
            return f"Trade {trade.get('trade_id', 'Unknown')}: Error creating summary"

    def get_trade_desk(self, trade: Dict[str, Any]) -> str:
        """
        Extract the trading desk from the trade data.
        Uses the execution_decision_maker from regulatory.mifid_ii as the desk.
        """
        try:
            regulatory = trade.get("regulatory", {})
            mifid_ii = regulatory.get("mifid_ii", {})
            desk = mifid_ii.get("execution_decision_maker", "general")
            return desk
        except Exception as e:
            self.logger.error(
                f"Error extracting desk from trade {trade.get('trade_id', 'Unknown')}: {str(e)}")
            return "general"

    def vectorize_trade(self, trade: Dict[str, Any]) -> bool:
        """
        Send a single trade to the vector DB via HTTP API.
        """
        try:
            # Create trade summary
            trade_summary = self.create_trade_summary(trade)

            # Get trading desk
            desk = self.get_trade_desk(trade)

            # Prepare URL parameters
            params = {
                "document": trade_summary,
                "document_type": "trade",
                "desk": desk
            }

            # URL encode parameters
            query_string = urllib.parse.urlencode(params)
            url = f"{self.vector_db_base_url}/add_document?{query_string}"

            # Make HTTP request
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Check response
            result = response.json()
            if "ok" in result or "OK" in result:
                self.logger.info(
                    f"Successfully vectorized trade {trade.get('trade_id', 'Unknown')} for desk {desk}")
                return True
            else:
                self.logger.error(
                    f"Failed to vectorize trade {trade.get('trade_id', 'Unknown')}: {result}")
                return False

        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"HTTP error vectorizing trade {trade.get('trade_id', 'Unknown')}: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(
                f"Error vectorizing trade {trade.get('trade_id', 'Unknown')}: {str(e)}")
            return False

    def vectorize_all_trades(self) -> Dict[str, Any]:
        """
        Iterate over all trades and vectorize them.
        Returns a summary of the vectorization process.
        """
        try:
            # Get all trades using wildcard pattern
            all_trades_result = self.trade_service.get_trades("trade_id", "*")

            if "error" in all_trades_result:
                self.logger.error(
                    f"Error retrieving trades: {all_trades_result['error']}")
                return {"error": all_trades_result["error"]}

            trades = all_trades_result.get("trades", [])
            total_trades = len(trades)

            if total_trades == 0:
                self.logger.warning("No trades found to vectorize")
                return {"message": "No trades found", "total_trades": 0, "successful": 0, "failed": 0}

            self.logger.info(
                f"Starting vectorization of {total_trades} trades")

            successful = 0
            failed = 0
            failed_trades = []

            for i, trade in enumerate(trades, 1):
                trade_id = trade.get("trade_id", f"Trade_{i}")
                self.logger.info(
                    f"Vectorizing trade {i}/{total_trades}: {trade_id}")

                if self.vectorize_trade(trade):
                    successful += 1
                else:
                    failed += 1
                    failed_trades.append(trade_id)

                # Log progress every 50 trades
                if i % 50 == 0:
                    self.logger.info(
                        f"Progress: {i}/{total_trades} trades processed ({successful} successful, {failed} failed)")

            # Final summary
            summary = {
                "message": f"Vectorization complete",
                "total_trades": total_trades,
                "successful": successful,
                "failed": failed,
                "success_rate": f"{(successful/total_trades)*100:.1f}%" if total_trades > 0 else "0%"
            }

            if failed_trades:
                # Show first 10 failed trades
                summary["failed_trade_ids"] = failed_trades[:10]
                if len(failed_trades) > 10:
                    summary["additional_failures"] = len(failed_trades) - 10

            self.logger.info(f"Vectorization summary: {summary}")
            return summary

        except Exception as e:
            error_msg = f"Error during trade vectorization: {str(e)}"
            self.logger.error(error_msg)
            return {"error": error_msg}


def main():
    """
    Example usage of the TradeVectorizer.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("TradeVectorizerExample")

    # Configure trade service
    config = {
        TradeService.ConfigField.DB_NAME.value: "trades.json",
        TradeService.ConfigField.DB_PATH.value: "python/src/server/trade_service",
        TradeService.ConfigField.SERVER_NAME.value: "TradeService"
    }

    try:
        # Initialize trade service
        trade_service = TradeService(logger, config)

        # Initialize vectorizer
        vectorizer = TradeVectorizer(trade_service)

        # Vectorize all trades
        result = vectorizer.vectorize_all_trades()

        print("\nVectorization Result:")
        print(json.dumps(result, indent=2))

    except Exception as e:
        logger.error(f"Failed to run trade vectorization: {str(e)}")


if __name__ == "__main__":
    main()
