from typing import List, Tuple


class Products:
    """Class to handle product-related static data operations."""
    
    _products: List[Tuple[str, str]] = [
        ("EQ", "Cash Equity"),
        ("DR", "Depositary Receipt"),
        ("OP", "Listed Option"),
        ("ET", "Exchange Traded Future"),
        ("FX", "Foreign Exchange")
    ]

    def get_all_product_type_codes(self) -> List[str]:
        """Get all product type codes."""
        return [code for code, _ in self._products]

    def get_product_type_description(self, code: str) -> str | None:
        """Get product type description for a given product code.
        
        Args:
            code: The product code to get the description for
            
        Returns:
            The product description if found, None otherwise
        """
        for product_code, desc in self._products:
            if product_code == code:
                return desc
        return None

    def get_all_products(self) -> List[Tuple[str, str]]:
        """Get all products as (code, description) tuples."""
        return self._products.copy()

    def product_exists(self, code: str) -> bool:
        """Check if a product code exists.
        
        Args:
            code: The product code to check
            
        Returns:
            True if the product exists, False otherwise
        """
        return any(c == code for c, _ in self._products)