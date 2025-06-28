from typing import List


class Currencies:
    """Class to handle currency-related static data operations."""
    
    _currencies: List[str] = ["USD", "GBP", "JPY",
                              "EUR", "AUD", "HKD",
                              "CAD", "CNY"]

    def get_all_currencies(self) -> List[str]:
        """Get all currencies."""
        return self._currencies.copy()

    def currency_exists(self, currency: str) -> bool:
        """Check if a currency exists.
        
        Args:
            currency: The currency code to check
            
        Returns:
            True if the currency exists, False otherwise
        """
        return currency in self._currencies