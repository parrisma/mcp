from enum import Enum
from shutil import register_archive_format
from typing import Any


class Permissions:

    class UserRole(Enum):
        SALES_TRADER = "Sales Trader"
        EXECUTION_TRADER = "Execution Trader"
        OPERATIONS = "Operations"
        FINANCE = "Finance"
        TECHNOLOGY = "Technology"
        COMPLIANCE = "Compliance"
        RESEARCH = "Research"

    class Capability(Enum):
        TRADES = "trades"
        INSRUMENTS = "instruments"
        NEWS = "news"
        RESEARCH = "research"
        CLIENTS = "clients"
        MESSAGES = "messages"
        DATAMINE = "datamine"

    class Action(Enum):
        READ = "read"
        WRITE = "write"

    _permissions: dict[str, Any] = {
        UserRole.SALES_TRADER.value: [{Capability.TRADES.value: Action.READ.value},
                                      {Capability.INSRUMENTS.value: Action.READ.value},
                                      {Capability.NEWS.value: Action.READ.value},
                                      {Capability.RESEARCH.value: Action.READ.value},
                                      {Capability.CLIENTS.value: Action.READ.value},
                                      {Capability.MESSAGES.value: Action.WRITE.value},
                                      {Capability.DATAMINE.value: Action.READ.value}],
        UserRole.EXECUTION_TRADER.value: [{Capability.TRADES.value: Action.WRITE.value},
                                          {Capability.INSRUMENTS.value: Action.READ.value},
                                          {Capability.NEWS.value: Action.READ.value},
                                          {Capability.RESEARCH.value: Action.READ.value},
                                          {Capability.CLIENTS.value: Action.READ.value},
                                          {Capability.MESSAGES.value: Action.WRITE.value},
                                          {Capability.DATAMINE.value: Action.READ.value}],
        UserRole.OPERATIONS.value: [{Capability.TRADES.value: Action.READ.value},
                                    {Capability.INSRUMENTS.value: Action.WRITE.value},
                                    {Capability.NEWS.value: Action.READ.value},
                                    {Capability.RESEARCH.value: Action.READ.value},
                                    {Capability.CLIENTS.value: Action.WRITE.value},
                                    {Capability.MESSAGES.value: Action.WRITE.value},
                                    {Capability.DATAMINE.value: Action.READ.value}],
        UserRole.FINANCE.value: [{Capability.TRADES.value: Action.READ.value},
                                 {Capability.INSRUMENTS.value: Action.READ.value},
                                 {Capability.NEWS.value: Action.READ.value},
                                 {Capability.RESEARCH.value: Action.READ.value},
                                 {Capability.CLIENTS.value: Action.READ.value},
                                 {Capability.MESSAGES.value: Action.WRITE.value},
                                 {Capability.DATAMINE.value: Action.READ.value}],
        UserRole.TECHNOLOGY.value: [{Capability.TRADES.value: Action.READ.value},
                                    {Capability.INSRUMENTS.value: Action.READ.value},
                                    {Capability.NEWS.value: Action.READ.value},
                                    {Capability.RESEARCH.value: Action.READ.value},
                                    {Capability.CLIENTS.value: Action.READ.value},
                                    {Capability.MESSAGES.value: Action.WRITE.value},
                                    {Capability.DATAMINE.value: Action.READ.value}],
        UserRole.COMPLIANCE.value: [{Capability.TRADES.value: Action.READ.value},
                                    {Capability.INSRUMENTS.value: Action.READ.value},
                                    {Capability.NEWS.value: Action.READ.value},
                                    {Capability.RESEARCH.value: Action.READ.value},
                                    {Capability.CLIENTS.value: Action.READ.value},
                                    {Capability.MESSAGES.value: Action.WRITE.value},
                                    {Capability.DATAMINE.value: Action.READ.value}],
        UserRole.RESEARCH.value: [{Capability.TRADES.value: Action.READ.value},
                                  {Capability.INSRUMENTS.value: Action.READ.value},
                                  {Capability.NEWS.value: Action.WRITE.value},
                                  {Capability.RESEARCH.value: Action.WRITE.value},
                                  {Capability.CLIENTS.value: Action.READ.value},
                                  {Capability.MESSAGES.value: Action.WRITE.value},
                                  {Capability.DATAMINE.value: Action.READ.value}]
    }

    def get_roles(self) -> list[str]:
        return [role.value for role in self.UserRole]

    def get_permissions(self, role: str) -> list[dict[str, str]]:
        if role in self._permissions:
            return self._permissions[role]
        else:
            raise ValueError(f"Role '{role}' does not exist in permissions.")
