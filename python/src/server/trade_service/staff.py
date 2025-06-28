from typing import List, Tuple
from enum import Enum


class Staff:
    class StaffType(Enum):
        SALES_TRADER_TYPE = "TDS"
        EXECUTION_TRADER_TYPE = "TRD"
        OPERATIONS_TYPE = "OPS"
        FINANCE_TYPE = "FIN"
        TECHNOLOGY_TYPE = "TEC"
        COMPLIANCE_TYPE = "CPM"
        RESEARCH = "RES"

    _staff_type_description: dict[str, str] = {
        "TDS": "Sales Traders - Client-facing professionals who execute trades and provide market insights to institutional clients",
        "TRD": "Execution Traders - Specialists focused on optimal trade execution and market timing strategies",
        "OPS": "Operations - Back-office professionals handling trade settlement, reconciliation, and operational processes",
        "FIN": "Finance - Financial analysts and controllers managing P&L, risk reporting, and financial controls",
        "TEC": "Technology - IT professionals maintaining trading systems, market data feeds, and technical infrastructure",
        "CPM": "Compliance - Regulatory specialists ensuring adherence to trading rules, risk limits, and regulatory requirements",
        "RES": "Research - Equity research analysts providing fundamental analysis, market insights, and investment recommendations"
    }

    _staff: List[Tuple[str, str, str]] = [
        # Traders (TRD)
        ("TRD_HK_001", "Alice Johnson", "Desk001"),
        ("TRD_HK_002", "Bob Smith", "Desk001"),
        ("TRD_NY_003", "Charlie Brown", "Desk001"),
        ("TRD_SY_004", "Diana Prince", "Desk001"),
        ("TRD_SY_005", "Ethan Hunt", "Desk001"),
        ("TRD_SG_006", "Fiona Gallagher", "Desk001"),
        ("TRD_SG_007", "George Costanza", "Desk001"),
        ("TRD_LN_008", "Hannah Montana", "Desk001"),
        ("TRD_LN_009", "Ian Malcolm", "Desk001"),
        ("TRD_HK_010", "Julia Roberts", "Desk001"),
        ("TRD_TK_011", "Yuki Tanaka", "Desk002"),
        ("TRD_FR_012", "Sophie Dubois", "Desk003"),
        ("TRD_DE_013", "Lukas Schneider", "Desk004"),
        ("TRD_BR_014", "Gabriel Silva", "Desk005"),
        ("TRD_IN_015", "Priya Sharma", "Desk006"),
        ("TRD_CN_016", "Wei Zhang", "Desk007"),
        ("TRD_RU_017", "Anastasia Ivanova", "Desk008"),
        ("TRD_AU_018", "Liam Wilson", "Desk009"),
        ("TRD_ZA_019", "Thabo Nkosi", "Desk010"),
        ("TRD_IT_020", "Giulia Romano", "Desk002"),
        # Sales Traders (TDS)
        ("TDS_NY_021", "Marcus Thompson", "Desk001"),
        ("TDS_LN_022", "Sarah Williams", "Desk002"),
        ("TDS_HK_023", "David Chen", "Desk003"),
        ("TDS_SG_024", "Emma Rodriguez", "Desk004"),
        ("TDS_TK_025", "James Mitchell", "Desk005"),
        # Operations (OPS)
        ("OPS_NY_026", "Lisa Anderson", "Operations"),
        ("OPS_LN_027", "Michael Brown", "Operations"),
        ("OPS_HK_028", "Jennifer Davis", "Operations"),
        ("OPS_SG_029", "Robert Wilson", "Operations"),
        ("OPS_TK_030", "Amanda Taylor", "Operations"),
        # Finance (FIN)
        ("FIN_NY_031", "Christopher Lee", "Finance"),
        ("FIN_LN_032", "Michelle Garcia", "Finance"),
        ("FIN_HK_033", "Daniel Martinez", "Finance"),
        ("FIN_SG_034", "Jessica White", "Finance"),
        ("FIN_TK_035", "Kevin Johnson", "Finance"),
        # Technology (TEC)
        ("TEC_NY_036", "Rachel Kim", "Technology"),
        ("TEC_LN_037", "Steven Clark", "Technology"),
        ("TEC_HK_038", "Nicole Wong", "Technology"),
        ("TEC_SG_039", "Brian Liu", "Technology"),
        ("TEC_TK_040", "Samantha Park", "Technology"),
        # Compliance (CPM)
        ("CPM_NY_041", "Thomas Green", "Compliance"),
        ("CPM_LN_042", "Ashley Moore", "Compliance"),
        ("CPM_HK_043", "Jonathan Zhang", "Compliance"),
        ("CPM_SG_044", "Rebecca Tan", "Compliance"),
        ("CPM_TK_045", "Matthew Singh", "Compliance"),
        # Research (RES)
        ("RES_NY_046", "Dr. Sarah Mitchell", "Research"),
        ("RES_LN_047", "Alexander Thompson", "Research"),
        ("RES_HK_048", "Maria Rodriguez", "Research")
    ]

    # Access control: List of (staff_id, desk) tuples
    # Each tuple grants the staff member access to data for that desk
    _access: List[Tuple[str, str]] = [
        # TRD (Execution Traders) - Access to their assigned desk
        ("TRD_HK_001", "Desk001"),
        ("TRD_HK_002", "Desk001"),
        ("TRD_NY_003", "Desk001"),
        ("TRD_SY_004", "Desk001"),
        ("TRD_SY_005", "Desk001"),
        ("TRD_SG_006", "Desk001"),
        ("TRD_SG_007", "Desk001"),
        ("TRD_LN_008", "Desk001"),
        ("TRD_LN_009", "Desk001"),
        ("TRD_HK_010", "Desk001"),
        ("TRD_TK_011", "Desk002"),
        ("TRD_FR_012", "Desk003"),
        ("TRD_DE_013", "Desk004"),
        ("TRD_BR_014", "Desk005"),
        ("TRD_IN_015", "Desk006"),
        ("TRD_CN_016", "Desk007"),
        ("TRD_RU_017", "Desk008"),
        ("TRD_AU_018", "Desk009"),
        ("TRD_ZA_019", "Desk010"),
        ("TRD_IT_020", "Desk002"),

        # TDS (Sales Traders) - Access to their assigned desk
        ("TDS_NY_021", "Desk001"),
        ("TDS_LN_022", "Desk002"),
        ("TDS_HK_023", "Desk003"),
        ("TDS_SG_024", "Desk004"),
        ("TDS_TK_025", "Desk005"),

        # OPS (Operations) - Distributed access covering all desks
        ("OPS_NY_026", "Desk001"),  # Large Cap Equities
        ("OPS_NY_026", "Desk002"),  # Small/Mid Cap Equities
        ("OPS_NY_026", "Desk003"),  # Equity Derivatives
        ("OPS_LN_027", "Desk004"),  # Equity Index
        ("OPS_LN_027", "Desk005"),  # Emerging Markets Equities
        ("OPS_LN_027", "Desk006"),  # Quantitative Equities
        ("OPS_HK_028", "Desk007"),  # Program Trading
        ("OPS_HK_028", "Desk008"),  # Equity Market Making
        ("OPS_SG_029", "Desk009"),  # ETF Trading
        ("OPS_SG_029", "Desk010"),  # Equity Sector Rotation
        ("OPS_TK_030", "Desk001"),  # Large Cap Equities (overlap for coverage)
        ("OPS_TK_030", "Desk005"),  # Emerging Markets Equities (overlap)

        # FIN (Finance) - Distributed access covering all desks
        ("FIN_NY_031", "Desk001"),  # Large Cap Equities
        ("FIN_NY_031", "Desk002"),  # Small/Mid Cap Equities
        ("FIN_LN_032", "Desk003"),  # Equity Derivatives
        ("FIN_LN_032", "Desk004"),  # Equity Index
        ("FIN_HK_033", "Desk005"),  # Emerging Markets Equities
        ("FIN_HK_033", "Desk006"),  # Quantitative Equities
        ("FIN_SG_034", "Desk007"),  # Program Trading
        ("FIN_SG_034", "Desk008"),  # Equity Market Making
        ("FIN_TK_035", "Desk009"),  # ETF Trading
        ("FIN_TK_035", "Desk010"),  # Equity Sector Rotation

        # TEC (Technology) - Distributed access covering all desks
        ("TEC_NY_036", "Desk001"),  # Large Cap Equities
        ("TEC_NY_036", "Desk007"),  # Program Trading
        ("TEC_LN_037", "Desk002"),  # Small/Mid Cap Equities
        ("TEC_LN_037", "Desk008"),  # Equity Market Making
        ("TEC_HK_038", "Desk003"),  # Equity Derivatives
        ("TEC_HK_038", "Desk009"),  # ETF Trading
        ("TEC_SG_039", "Desk004"),  # Equity Index
        ("TEC_SG_039", "Desk010"),  # Equity Sector Rotation
        ("TEC_TK_040", "Desk005"),  # Emerging Markets Equities
        ("TEC_TK_040", "Desk006"),  # Quantitative Equities

        # CPM (Compliance) - Distributed access covering all desks
        ("CPM_NY_041", "Desk001"),  # Large Cap Equities
        ("CPM_NY_041", "Desk002"),  # Small/Mid Cap Equities
        ("CPM_NY_041", "Desk003"),  # Equity Derivatives
        ("CPM_LN_042", "Desk004"),  # Equity Index
        ("CPM_LN_042", "Desk005"),  # Emerging Markets Equities
        ("CPM_HK_043", "Desk006"),  # Quantitative Equities
        ("CPM_HK_043", "Desk007"),  # Program Trading
        ("CPM_SG_044", "Desk008"),  # Equity Market Making
        ("CPM_SG_044", "Desk009"),  # ETF Trading
        ("CPM_TK_045", "Desk010"),  # Equity Sector Rotation

        # Additional random access for TRD and TDS to multiple desks
        ("TRD_HK_001", "Desk002"),  # Also has access to Small/Mid Cap
        ("TRD_HK_001", "Desk003"),  # Also has access to Derivatives
        ("TRD_NY_003", "Desk004"),  # Also has access to Index
        ("TRD_SY_004", "Desk005"),  # Also has access to Emerging Markets
        ("TRD_SG_006", "Desk006"),  # Also has access to Quantitative
        ("TRD_LN_008", "Desk007"),  # Also has access to Program Trading
        ("TRD_TK_011", "Desk001"),  # Also has access to Large Cap
        ("TRD_TK_011", "Desk008"),  # Also has access to Market Making
        ("TRD_FR_012", "Desk009"),  # Also has access to ETF
        ("TRD_DE_013", "Desk010"),  # Also has access to Sector Rotation
        ("TRD_BR_014", "Desk001"),  # Also has access to Large Cap
        ("TRD_IN_015", "Desk002"),  # Also has access to Small/Mid Cap
        ("TRD_CN_016", "Desk003"),  # Also has access to Derivatives
        ("TRD_RU_017", "Desk004"),  # Also has access to Index
        ("TRD_AU_018", "Desk005"),  # Also has access to Emerging Markets
        ("TRD_IT_020", "Desk006"),  # Also has access to Quantitative

        ("TDS_NY_021", "Desk002"),  # Also has access to Small/Mid Cap
        ("TDS_NY_021", "Desk003"),  # Also has access to Derivatives
        ("TDS_LN_022", "Desk001"),  # Also has access to Large Cap
        ("TDS_LN_022", "Desk004"),  # Also has access to Index
        ("TDS_HK_023", "Desk005"),  # Also has access to Emerging Markets
        ("TDS_SG_024", "Desk006"),  # Also has access to Quantitative
        ("TDS_TK_025", "Desk007"),  # Also has access to Program Trading
        ("TDS_TK_025", "Desk008"),  # Also has access to Market Making

        # RES (Research) - Broad access across multiple desks for comprehensive analysis
        ("RES_NY_046", "Desk001"),  # Large Cap Equities
        ("RES_NY_046", "Desk002"),  # Small/Mid Cap Equities
        ("RES_NY_046", "Desk003"),  # Equity Derivatives
        ("RES_NY_046", "Desk004"),  # Equity Index
        ("RES_LN_047", "Desk005"),  # Emerging Markets Equities
        ("RES_LN_047", "Desk006"),  # Quantitative Equities
        ("RES_LN_047", "Desk007"),  # Program Trading
        ("RES_LN_047", "Desk008"),  # Equity Market Making
        ("RES_HK_048", "Desk009"),  # ETF Trading
        ("RES_HK_048", "Desk010"),  # Equity Sector Rotation
        ("RES_HK_048", "Desk001"),  # Large Cap Equities (overlap for Asia coverage)
        ("RES_HK_048", "Desk005"),  # Emerging Markets Equities (overlap for Asia coverage)
    ]

    @classmethod
    def get_all_staff_types_with_descriptions(cls) -> List[Tuple[str, str]]:
        return [(staff_type.value, cls._staff_type_description[staff_type.value])
                for staff_type in cls.StaffType]

    @classmethod
    def get_staff_by_type(cls, staff_type: str) -> List[Tuple[str, str, str]]:
        return [staff for staff in cls._staff if staff[0].startswith(staff_type)]

    @classmethod
    def get_staff_type_description(cls, staff_code: str) -> str | None:
        return cls._staff_type_description.get(staff_code)

    def get_all_traders(self) -> List[str]:
        return [code for code, _, _ in self._staff]

    def get_trader_description(self, code: str) -> str | None:
        for c, name, desk in self._staff:
            if c == code:
                return f"{name} ({desk})"
        return None

    def get_trader_info(self, code: str) -> Tuple[str, str] | None:
        for c, name, desk in self._staff:
            if c == code:
                return (name, desk)
        return None

    def get_all_trader_data(self) -> List[Tuple[str, str, str]]:
        return self._staff.copy()

    def trader_exists(self, code: str) -> bool:
        return any(c == code for c, _, _ in self._staff)

    @classmethod
    def get_desks_staff_has_access_to(cls, staff_id: str) -> List[str]:
        return [desk for sid, desk in cls._access if sid == staff_id]

    @classmethod
    def get_staff_who_have_access_to_desk(cls, desk_code: str) -> List[str]:
        return [staff_id for staff_id, desk in cls._access if desk == desk_code]

    @classmethod
    def does_staff_id_have_desk_access(cls, staff_id: str, desk_code: str) -> bool:
        return (staff_id, desk_code) in cls._access
