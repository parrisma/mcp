from typing import List, Tuple


class AlgoStrategies:
    """Class to handle algorithmic trading strategy-related static data operations."""
    
    _algo_strategies: List[Tuple[str, str]] = [
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

    def get_all_algo_types(self) -> List[str]:
        """Get all algorithmic strategy codes."""
        return [code for code, _ in self._algo_strategies]

    def get_algo_description(self, code: str) -> str | None:
        """Get algorithm description for a given algo code.
        
        Args:
            code: The algorithm code to get the description for
            
        Returns:
            The algorithm description if found, None otherwise
        """
        for c, desc in self._algo_strategies:
            if c == code:
                return desc
        return None

    def get_all_algo_strategies(self) -> List[Tuple[str, str]]:
        """Get all algo strategies as (code, description) tuples."""
        return self._algo_strategies.copy()

    def algo_strategy_exists(self, code: str) -> bool:
        """Check if an algo strategy code exists.
        
        Args:
            code: The algo strategy code to check
            
        Returns:
            True if the algo strategy exists, False otherwise
        """
        return any(c == code for c, _ in self._algo_strategies)