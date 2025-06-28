from typing import List, Tuple


class Desks:
    """Class to handle trading desk-related static data operations."""
    
    _desks: List[Tuple[str, str]] = [
        ("Desk001", "Large Cap Equities Desk"),
        ("Desk002", "Small/Mid Cap Equities Desk"),
        ("Desk003", "Equity Derivatives Desk"),
        ("Desk004", "Equity Index Desk"),
        ("Desk005", "Emerging Markets Equities Desk"),
        ("Desk006", "Quantitative Equities Desk"),
        ("Desk007", "Program Trading Desk"),
        ("Desk008", "Equity Market Making Desk"),
        ("Desk009", "ETF Trading Desk"),
        ("Desk010", "Equity Sector Rotation Desk")
    ]

    def get_all_desks(self) -> List[str]:
        """Get all desk codes."""
        return [code for code, _ in self._desks]

    def get_desk_description(self, code: str) -> str | None:
        """Get desk description for a given desk code.
        
        Args:
            code: The desk code to get the description for
            
        Returns:
            The desk description if found, None otherwise
        """
        for c, desc in self._desks:
            if c == code:
                return desc
        return None

    def get_all_desk_data(self) -> List[Tuple[str, str]]:
        """Get all desks as (code, description) tuples."""
        return self._desks.copy()

    def desk_exists(self, code: str) -> bool:
        """Check if a desk code exists.
        
        Args:
            code: The desk code to check
            
        Returns:
            True if the desk exists, False otherwise
        """
        return any(c == code for c, _ in self._desks)