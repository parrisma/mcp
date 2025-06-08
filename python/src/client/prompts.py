import os
import logging
import uuid
import json
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Protocol, List, Any
from datetime import datetime
from langchain.prompts import PromptTemplate


class Prompts:

    class MakePromptTemplate(Protocol):
        def __call__(self,
                     prompt_template_as_text: str,
                     variable_names: List[str]) -> PromptTemplate: ...

    class LoadTemplateFragments(Protocol):
        def __call__(self) -> Dict[str, Any]: ...

    class PromptSettings(Enum):
        TEMPLATE_FOLDER = "prompt_templates"
        DEFAULT = "prompt_template_default.txt"
        SERVER_DEFINITION = "prompt_template_server_defintion.txt"
        DEFAULT_PROMPT = "default"

        def __str__(self) -> str:
            return self.value

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

    def _load_default_fragments(self) -> Dict[str, Any]:
        try:
            mcp_server_definition_file: Path = Path(
                self._template_root_folder / self.PromptSettings.SERVER_DEFINITION.value)
            if not mcp_server_definition_file.is_file():
                raise ValueError(
                    f"Server definition file '{str(mcp_server_definition_file)}' does not exist.")
            mcp_server_definition = self._load_prompt_fragment(
                mcp_server_definition_file)
            if not mcp_server_definition:   # Check if the file is empty
                raise ValueError(
                    f"Server definition file '{str(mcp_server_definition_file)}' is empty.")
            return {"mcp_server_definition": mcp_server_definition}
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
                   session_id: str,
                   prompt_name: Optional[str] = None,
                   variables: Optional[Dict[str, Any]] = None,
                   loadTemplateFragments: Optional[LoadTemplateFragments] = None,
                   makePromptTemplate: Optional[MakePromptTemplate] = None) -> str:
        try:
            if not variables:
                variables = {}

            variables["goal"] = goal
            variables["session_id"] = session_id

            if makePromptTemplate is None:
                makePromptTemplate = self._make_default_prompt_template  # type: ignore

            if loadTemplateFragments is None:
                loadTemplateFragments = self._load_default_fragments
            fragment_variables: Dict[str, Any] = loadTemplateFragments()
            variables.update(fragment_variables)

            variable_names = list(variables.keys())
            prompt: PromptTemplate = makePromptTemplate(
                self._load_prompt_template(prompt_name),
                variable_names=variable_names)

            return prompt.format(**variables or {},)

        except Exception as e:
            raise ValueError(f"Error formatting prompt: {e}"
                             )

    def _log_prompt(self,
                    prompt: str) -> None:
        try:
            with open("prompt_log.txt", "a", encoding="utf-8") as f:
                f.write("=" * 80 + "\n\n")
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')}\n\n")
                f.write(prompt + "\n")
                f.write("=" * 80 + "\n\n")
        except Exception as e:
            self._log.error(f"Failed to log prompt: {e}")

    def build_prompt(self,
                     user_goal: str,
                     session_id: uuid.UUID,
                     mcp_server_descriptions: Dict[str, Any],
                     mcp_responses: List[Dict[str, Any]],
                     clarifications: List[Dict[str, Any]]
                     ) -> Optional[str]:
        try:
            prompt: str = self.get_prompt(
                goal=user_goal,
                session_id=str(session_id),
                variables={
                    "mcp_server_descriptions": json.dumps(mcp_server_descriptions),
                    "mcp_server_responses": json.dumps(mcp_responses, ensure_ascii=False, indent=2),
                    "clarification_responses": json.dumps(clarifications, ensure_ascii=False, indent=2)
                }
            )

            self._log_prompt(prompt)

            return prompt

        except Exception as e:
            msg: str = f"Error in forming fully qualified propmt: {e}"
            self._log.error(msg)
            return None


def tests() -> None:
    try:
        prompts = Prompts(template_root_folder=None,
                          default_prompt_file_name=None)
        test_prompt: str = prompts.get_prompt(
            goal="Test goal",
            session_id="12345",
            variables={"mcp_server_descriptions": '{"server1": "description1"}',
                       "mcp_server_responses": '{"response1": "data1"}',
                       "clarification_responses": '{"clarification1": "info1"}'},
            makePromptTemplate=None,
            prompt_name=None
        )
        print(f"Test prompt: {test_prompt}")

        print("Prompts instance created successfully.")
    except Exception as e:
        print(f"Failed to create Prompts instance: {e}")


if __name__ == "__main__":
    tests()
