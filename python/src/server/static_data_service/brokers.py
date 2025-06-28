from typing import List, Tuple


class Brokers:
    """Class to handle broker-related static data operations."""

    _brokers: List[Tuple[str, str]] = [
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

    def get_broker_description(self, code: str) -> str | None:
        for c, desc in self._brokers:
            if c == code:
                return desc
        return None

    def get_all_broker_data(self) -> List[Tuple[str, str]]:
        return self._brokers.copy()

    def get_all_broker_codes(self) -> List[str]:
        return [code for code, _ in self._brokers]

    def get_broker_name(self, code: str) -> str | None:
        for broker_code, name in self._brokers:
            if broker_code == code:
                return name
        return None

    def get_all_brokers(self) -> List[Tuple[str, str]]:
        return self._brokers.copy()

    def broker_exists(self, code: str) -> bool:
        return any(c == code for c, _ in self._brokers)
