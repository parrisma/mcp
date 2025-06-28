from typing import List, Tuple, Dict, Any
from pydantic import Field
from typing import Annotated


class Venues:
    """Class to handle venue-related static data operations."""
    
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

    def get_all_venue_codes(self) -> List[str]:
        """Get all venue codes."""
        return [code for code, _ in self._venues]

    def get_venue_description(self, code: str) -> str | None:
        """Get venue description for a given venue code.
        
        Args:
            code: The venue code to get the description for
            
        Returns:
            The venue description if found, None otherwise
        """
        for c, desc in self._venues:
            if c == code:
                return desc
        return None

    def get_all_venues(self) -> List[Tuple[str, str]]:
        """Get all venues as (code, description) tuples."""
        return self._venues.copy()

    def venue_exists(self, code: str) -> bool:
        """Check if a venue code exists.
        
        Args:
            code: The venue code to check
            
        Returns:
            True if the venue exists, False otherwise
        """
        return any(c == code for c, _ in self._venues)