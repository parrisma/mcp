import logging
import time
from typing import Callable, List, Tuple, Annotated, Dict, Any, Literal
from i_mcp_server import IMCPServer
from pydantic import Field
from langchain.prompts import PromptTemplate
import uuid


class HelloWorldServer(IMCPServer):
    def __init__(self,
                 logger: logging.Logger,
                 json_config: Dict[str, Any]) -> None:
        self._log: logging.Logger = logger
        self._config: Dict[str, Any] = json_config
        self._server_name: str = f"HelloWorldServer_{str(uuid.uuid4()).upper()}"

    @property
    def server_name(self) -> str:
        return self._server_name

    @property
    def supported_tools(self) -> List[Tuple[str, Callable]]:
        return [("add", self._add),
                ("multiply", self.multiply)
                ]

    @property
    def supported_resources(self) -> List[Tuple[str, Callable]]:
        return [("message", self.get_message),
                ("alive", self.alive)]

    @property
    def supported_prompts(self) -> List[Tuple[str, Callable]]:
        return [("sme", self.get_sme_prompt)]

    #
    # Tool implementions
    #

    def _add(self,
             a: Annotated[int, Field(description="First integer to add")],
             b: Annotated[int, Field(description="Second integer to add")]) -> int:
        self._log.info(f"Tool [add] - calculating {a} plus {b}")
        return a + b

    def multiply(self,
                 a: Annotated[int, Field(description="First integer to multiply")],
                 b: Annotated[int, Field(description="Second integer to multiply")]) -> int:
        self._log.info(f"Tool [Multiply] calculating {a} times {b}")
        return a * b

    #
    # Resource implementations
    #

    def get_message(self,
                    name: Annotated[str, Field(description="The name of teh person to generate the message for")]) -> str:
        self._log.info(f"Generating message for {name}")
        return f"Greetings, {name}!"

    def alive(self) -> Dict[str, Any]:
        self._log.info("Received a still alive request")
        return {
            "status": "ok",
            "timestamp": int(time.time()),  # time import is now present
            "version": self._config.get("serverInfo", {}).get("version", "unknown")
        }

    #
    # Prompt implementations
    #

    def get_sme_prompt(self,
                       topic: Annotated[Literal["coding", "math", "writing"], Field(description="Topics supported: coding, math, writing")],
                       subject: Annotated[str, Field(description="The subject to get details on for the given topic")]) -> str:
        self._log.info(
            f"Generating an SME prompt for topic: {topic}, subject: {subject}")
        prompts_config: Dict[str, str] = {
            "coding": "You are an expert programmer with deep knowledge of software development, please explain {subject}",
            "math": "You are a high school mathematics tutor, please explain {subject}",
            "writing": "You are a professional writer and editor with expertise in creative writing, please write a paragraph on {subject}"
        }
        template_str: str = prompts_config.get(str(topic).lower(
        ), "You are a helpful assistant. Please provide information about {subject}")
        prompt_template: PromptTemplate = PromptTemplate.from_template(
            template_str)
        return prompt_template.format(subject=subject)
