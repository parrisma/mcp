from enum import Enum


class Permissions:

    class UserRole(Enum):
        SALES_TRADER = "Sales Trader"
        EXECUTION_TRADER = "Execution Trader"
        OPERATIONS = "Operations"
        FINANCE = "Finance"
        TECHNOLOGY = "Technology"
        COMPLIANCE = "Compliance"

    def get_roles(self) -> list[str]:
        return [role.value for role in self.UserRole]
