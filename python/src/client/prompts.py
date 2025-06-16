import os
import logging
from tkinter import N
import uuid
import json
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Protocol, List, Any
from datetime import datetime
from flask import session
from langchain.prompts import PromptTemplate
import mcp
import random

from numpy import var


class Prompts:

    class MakePromptTemplate(Protocol):
        def __call__(self,
                     prompt_template_as_text: str,
                     variable_names: List[str]) -> PromptTemplate: ...

    class LoadTemplateFragments(Protocol):
        def __call__(self,
                     user_role: Optional[str]) -> Dict[str, Any]: ...

    class PromptSettings(Enum):
        TEMPLATE_FOLDER = "prompt_templates"
        DEFAULT = "prompt_template_default.txt"
        SERVER_DEFINITION = "prompt_template_server_defintion.txt"
        AI_SAFTEY_STATEMENT = "prompt_safety_statement.txt"
        # Default, should be overridden via login details.
        USER_ROLE_DEFINITION = "prompt_sales_trader_role_definition.txt"
        ORG_STATEMENT = "prompt_org_statement.txt"
        DEFAULT_PROMPT = "default"

        def __str__(self) -> str:
            return self.value

    class UserRole(Enum):
        SALES_TRADER = "Sales Trader"
        EXECUTION_TRADER = "Execution Trader"
        OPERATIONS = "Operations"
        FINANCE = "Finance"
        TECHNOLOGY = "Technology"
        COMPLIANCE = "Compliance"

        def __str__(self) -> str:
            return self.value

    role_to_fragment: Dict[str, str] = {
        UserRole.SALES_TRADER.value: "prompt_sales_trader_role_definition.txt",
        UserRole.EXECUTION_TRADER.value: "prompt_execution_trader_role_definition.txt",
        UserRole.OPERATIONS.value: "prompt_operations_role_definition.txt",
        UserRole.FINANCE.value: "prompt_finance_role_definition.txt",
        UserRole.TECHNOLOGY.value: "prompt_technology_role_definition.txt",
        UserRole.COMPLIANCE.value: "prompt_compliance_role_definition.txt",
    }

    def __init__(self,
                 template_root_folder: Optional[Path] = None,
                 default_prompt_file_name: Optional[str] = None) -> None:

        self._log: logging.Logger = logging.getLogger(__name__)
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(
                level=logging.INFO,  # Default to INFO, can be overridden by application
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler()]
            )

        self._prompt_version_by_session: Dict[uuid.UUID, int] = {}
        self._prompt_log_folder: Path = Path("prompt_logs")

        if template_root_folder:
            self._template_root_folder: Path = Path(template_root_folder)
        else:
            self._template_root_folder: Path = Path(
                os.path.dirname(__file__)) / self.PromptSettings.TEMPLATE_FOLDER.value

        if not Path(self._template_root_folder).is_dir():
            raise ValueError(
                f"Provided template_root_folder '{template_root_folder}' is not a valid directory.")

        self._prompts: Dict[str, Path] = {}

        # If default_prompt_file_name is given, use it as the default prompt if the file exists
        proposed_default_prompt_file_name: Path
        if default_prompt_file_name:
            proposed_default_prompt_file_name = Path(
                self._template_root_folder / default_prompt_file_name)
        else:
            proposed_default_prompt_file_name = Path(
                self._template_root_folder / self.PromptSettings.DEFAULT.value)

        if proposed_default_prompt_file_name.is_file():
            self._prompts[self.PromptSettings.DEFAULT_PROMPT.value] = proposed_default_prompt_file_name
        else:
            raise ValueError(
                f"Default prompt file '{default_prompt_file_name}' does not exist in the template folder.")

    def _make_default_prompt_template(self,
                                      prompt_template_as_text: str,
                                      variable_names: List[str]) -> PromptTemplate:
        return PromptTemplate(
            input_variables=variable_names,
            template=prompt_template_as_text
        )

    def _load_prompt_fragment(self,
                              fragment_file: Path) -> str:
        try:
            if not fragment_file.is_file():
                raise ValueError(
                    f"Server definition file '{str(fragment_file)}' does not exist.")
            with open(fragment_file, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as fne:
            raise ValueError(
                f"Server definition file not found.") from fne
        except Exception as e:  # pylint: disable=broad-except
            raise ValueError(
                f"An error occurred while loading the server definition: {e}") from e

    def _load_variables(self, **kwargs) -> Dict[str, Any]:
        variables: Dict[str, str] = {}
        try:
            for key, value in kwargs.items():
                if isinstance(value, Path):
                    variables[key] = self._load_prompt_fragment(value)
                else:
                    variables[key] = value
            return variables
        except Exception as e:  # pylint: disable=broad-except
            raise ValueError(
                f"An error occurred while loading default variables: {e}") from e

    def _load_default_fragments(self,
                                user_role: Optional[str]) -> Dict[str, Any]:
        all_fragments: Dict[str, Any] = {}
        if user_role is None:
            user_role_key = self.UserRole.SALES_TRADER.value
        else:
            user_role_key = user_role
        role_fragment_file: Optional[str] = self.role_to_fragment.get(
            user_role_key, None)
        if not role_fragment_file:
            raise ValueError(
                f"Role '{user_role}' is not defined in role_to_fragment mapping, so we cannot form a prompt.")
        try:
            for fragment_name, fragment_file in [("mcp_server_definition",
                                                  self.PromptSettings.SERVER_DEFINITION.value),
                                                 ("ai_saftey_statement",
                                                  self.PromptSettings.AI_SAFTEY_STATEMENT.value),
                                                 ("user_role_definition",
                                                  role_fragment_file),
                                                 ("org_statement",
                                                  self.PromptSettings.ORG_STATEMENT.value)]:

                fragment_full_file_and_path: Path = Path(
                    self._template_root_folder / fragment_file)
                if not fragment_full_file_and_path.is_file():
                    raise ValueError(
                        f"Prompt frgament file '{str(fragment_full_file_and_path)}' does not exist.")
                fragment = self._load_prompt_fragment(
                    fragment_full_file_and_path)
                if not fragment:   # Check if the file is empty
                    raise ValueError(
                        f"Prompt fragment '{str(fragment_full_file_and_path)}' is empty.")
                all_fragments[fragment_name] = fragment
            return all_fragments
        except Exception as e:  # pylint: disable=broad-except
            raise ValueError(
                f"An error occurred while loading default fragments: {e}") from e

    def _load_prompt_template(self,
                              prompt_name: Optional[str]) -> str:

        try:
            if prompt_name is None:
                prompt_name = self.PromptSettings.DEFAULT_PROMPT.value
            if prompt_name not in self._prompts:
                raise ValueError(
                    f"Prompt '{prompt_name}' is not defined in the prompts dictionary.")
            if not self._prompts[prompt_name].is_file():
                raise ValueError(
                    f"Prompt file '{str(self._prompts[prompt_name])}' does not exist.")
            file_name: Path = self._prompts[prompt_name]
            with open(file_name, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as fne:
            raise ValueError(
                f"Prompt template file not found.") from fne
        except Exception as e:  # pylint: disable=broad-except
            raise ValueError(
                f"An error occurred while loading the prompt template: {e}") from e

    def get_prompt(self,
                   goal: str,
                   user_role: str,
                   staff_id: str,
                   session_id: str,
                   prompt_name: Optional[str] = None,
                   variables: Optional[Dict[str, Any]] = None,
                   loadTemplateFragments: Optional[LoadTemplateFragments] = None,
                   makePromptTemplate: Optional[MakePromptTemplate] = None) -> str:
        try:
            if user_role not in [role.value for role in self.UserRole]:
                raise ValueError(
                    f"Role '{user_role}' is not defined in User Role")

            if not variables:
                variables = {}

            variables["goal"] = goal
            variables["session_id"] = session_id
            variables["staff_id"] = staff_id

            if makePromptTemplate is None:
                makePromptTemplate = self._make_default_prompt_template  # type: ignore

            if loadTemplateFragments is None:
                loadTemplateFragments = self._load_default_fragments
            fragment_variables: Dict[str, Any] = loadTemplateFragments(
                user_role=user_role)
            variables.update(fragment_variables)

            variable_names = list(variables.keys())
            prompt: PromptTemplate = makePromptTemplate(
                self._load_prompt_template(prompt_name),
                variable_names=variable_names)

            return prompt.format(**variables or {},)

        except Exception as e:
            raise ValueError(f"Error formatting prompt: {e}"
                             )

    def extract_version(self,
                        prompt_log_file_name: Path) -> int:
        try:
            return int(str(prompt_log_file_name).split("_")[-1].split(".")[0])
        except Exception:
            return 0

    def get_prompts_by_session_id(self,
                                  session_id: uuid.UUID) -> Dict[str, str]:
        try:
            session_files = list(Path(self._prompt_log_folder).glob(
                f"prompt_{str(session_id)}_*.txt"))
            session_files.sort(key=self.extract_version)
            return {str(f): f.read_text(encoding="utf-8") for f in session_files if f.is_file()}
        except Exception as e:
            self._log.error(f"Failed to log prompt: {e}")
            return {}

    def _log_prompt(self,
                    session_id: uuid.UUID,
                    prompt: str) -> None:
        try:
            prompt_version: int = self._prompt_version_by_session.get(
                session_id, 0) + 1
            self._prompt_version_by_session[session_id] = prompt_version
            self._log.info(
                f"Logging prompt version {prompt_version} for session {session_id}")

            prompt_log_file_name: Path = Path(
                self._prompt_log_folder) / f"prompt_{str(session_id)}_{prompt_version}.txt"
            with open(prompt_log_file_name, "a", encoding="utf-8") as f:
                f.write("=" * 80 + "\n\n")
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}\n\n")
                f.write(prompt + "\n")
                f.write("=" * 80 + "\n\n")
        except Exception as e:
            self._log.error(f"Failed to log prompt: {e}")

    def build_prompt(self,
                     user_goal: str,
                     session_id: uuid.UUID,
                     user_role: str,
                     staff_id: str,
                     mcp_server_descriptions: Dict[str, Any],
                     mcp_responses: List[Dict[str, Any]],
                     clarifications: List[Dict[str, Any]]
                     ) -> Optional[str]:
        try:
            prompt: str = self.get_prompt(
                goal=user_goal,
                user_role=user_role,
                staff_id=staff_id,
                session_id=str(session_id),
                variables={
                    "mcp_server_descriptions": json.dumps(mcp_server_descriptions),
                    "mcp_server_responses": json.dumps(mcp_responses, ensure_ascii=False, indent=2),
                    "clarification_responses": json.dumps(clarifications, ensure_ascii=False, indent=2)
                }
            )

            self._log_prompt(session_id=session_id,
                             prompt=prompt)

            return prompt

        except Exception as e:
            msg: str = f"Error in forming fully qualified propmt: {e}"
            self._log.error(msg)
            return None


def tests() -> None:
    try:
        prompts = Prompts(template_root_folder=None,
                          default_prompt_file_name=None)
        session_id: uuid.UUID = uuid.uuid4()
        roles_list = [role.value for role in Prompts.UserRole]
        print(f"Available roles: {roles_list}")
        for i in range(3):
            user_role = random.choice(roles_list)
            test_prompt: str | None = prompts.build_prompt(
                user_goal=f"Test goal {i}",
                session_id=session_id,
                staff_id=f"staff_{i}", # Dummy
                user_role=user_role,
                mcp_server_descriptions={f"server{i}": "description1"},
                mcp_responses=[{f"response{i}": "data1"}],
                clarifications=[{f"clarification{i}": "info1"}]
            )
            if test_prompt is not None:
                print(f"Test prompt: {test_prompt}")
            else:
                print("Test prompt generation failed.")

        for k in prompts.get_prompts_by_session_id(session_id).keys():
            print(f"Prompt file: {k}")

        print("Prompts instance created successfully.")
    except Exception as e:
        print(f"Failed to create Prompts instance: {e}")


if __name__ == "__main__":
    tests()
