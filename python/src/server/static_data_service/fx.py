from typing import Optional, Mapping

# Default rates: 1 unit of KEY currency = VALUE units of USD.
# Example: "EUR": 1.08 means 1 EUR = 1.08 USD.
_DEFAULT_RATES_VS_USD: Mapping[str, float] = {
    "USD": 1.0,
    "GBP": 0.74,
    "JPY": 144.14,
    "EUR": 0.87,
    "AUD": 1.54,
    "HKD": 7.85,
    "CAD": 1.36,
    "CNY": 7.17
}


class FxConverter:
    """
    A class to convert amounts between different currencies using a set of
    exchange rates provided against a common base currency.
    """

    def __init__(self,
                 rates_data: Optional[Mapping[str, float]] = None,
                 base_currency: str = "USD"):
        """
        Initializes the FxConverter.

        Args:
            rates_data: A dictionary where keys are currency codes (e.g., "EUR")
                        and values are their rates against the base_currency.
                        (e.g., if base_currency is "USD" and "EUR": 1.08 is provided,
                        it means 1 EUR = 1.08 USD).
                        If None, default rates against USD will be used.
            base_currency: The base currency against which rates in rates_data are quoted.
                           Defaults to "USD".
        """
        raw_rates_data: Mapping[str, float]
        if rates_data is None:
            raw_rates_data = _DEFAULT_RATES_VS_USD
        else:
            raw_rates_data = rates_data

        # Store rates internally, ensuring keys are uppercase and values are floats.
        # These rates represent: 1 unit of KEY_CURRENCY = VALUE units of BASE_CURRENCY.
        self.__rates_vs_base: dict[str, float] = {
            str(k).upper(): float(v) for k, v in raw_rates_data.items()
        }
        self.__base_currency: str = str(base_currency).upper()

    def get_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Calculates the exchange rate from from_currency to to_currency.
        The rate returned signifies how many units of to_currency are
        equivalent to 1 unit of from_currency.

        Args:
            from_currency: The currency code to convert from (e.g., "USD").
            to_currency: The currency code to convert to (e.g., "EUR").

        Returns:
            The exchange rate as a float, or None if the conversion is not possible
            (e.g., unsupported currency, division by zero).
        """
        from_ccy = str(from_currency).upper()
        to_ccy = str(to_currency).upper()

        if from_ccy == to_ccy:
            return 1.0

        # Get the value of 1 unit of from_currency in terms of the base currency.
        from_ccy_value_in_base: Optional[float]
        if from_ccy == self.__base_currency:
            from_ccy_value_in_base = 1.0
        else:
            from_ccy_value_in_base = self.__rates_vs_base.get(from_ccy)

        if from_ccy_value_in_base is None:
            # print(f"Warning: from_currency '{from_ccy}' not found in rates data.")
            return None

        # Get the value of 1 unit of to_currency in terms of the base currency.
        to_ccy_value_in_base: Optional[float]
        if to_ccy == self.__base_currency:
            to_ccy_value_in_base = 1.0
        else:
            to_ccy_value_in_base = self.__rates_vs_base.get(to_ccy)

        if to_ccy_value_in_base is None:
            # print(f"Warning: to_currency '{to_ccy}' not found in rates data.")
            return None

        if to_ccy_value_in_base == 0:
            # print(f"Warning: Rate for to_currency '{to_ccy}' against base is zero, cannot divide.")
            return None

        # To get rate FROM_CCY / TO_CCY:
        # (FROM_CCY / BASE_CURRENCY) / (TO_CCY / BASE_CURRENCY)
        # = from_ccy_value_in_base / to_ccy_value_in_base
        return from_ccy_value_in_base / to_ccy_value_in_base


if __name__ == '__main__':
    # Example Usage:
    converter = FxConverter()  # Uses default rates vs USD

    # Test cases
    print(f"USD to EUR: {converter.get_rate('USD', 'EUR')}")
    print(f"USD to HKD: {converter.get_rate('USD', 'HKD')}")
    print(f"EUR to USD: {converter.get_rate('EUR', 'USD')}")
    print(f"GBP to JPY: {converter.get_rate('GBP', 'JPY')}")
    print(f"JPY to GBP: {converter.get_rate('JPY', 'GBP')}")
    print(f"USD to USD: {converter.get_rate('USD', 'USD')}")
    print(f"EUR to EUR: {converter.get_rate('EUR', 'EUR')}")
    print(f"XXX to EUR: {converter.get_rate('XXX', 'EUR')}")
    print(f"EUR to YYY: {converter.get_rate('EUR', 'YYY')}")
