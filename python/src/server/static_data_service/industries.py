from typing import List


class Industries:
    """Class to handle industry-related static data operations."""
    
    _industries: List[str] = [
        "Technology", "Energy", "Healthcare", "Semiconductors", "Renewable Energy",
        "Financial Services", "Mining", "Automotive", "Retail", "Telecommunications",
        "Pharmaceuticals", "Entertainment", "Aerospace", "Biotechnology", "Agriculture"
    ]

    def get_all_industries(self) -> List[str]:
        """Get all industries."""
        return self._industries.copy()

    def industry_exists(self, industry: str) -> bool:
        """Check if an industry exists.
        
        Args:
            industry: The industry name to check
            
        Returns:
            True if the industry exists, False otherwise
        """
        return industry in self._industries