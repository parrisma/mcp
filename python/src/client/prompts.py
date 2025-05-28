from langchain.prompts import PromptTemplate

mcp_server_definition = """
{
  "MCP_Server": {
    "description": "An API that enables an LLM to retrieve data and execute predefined actions to improve responses.",
    "capabilities": [
      {
        "name": "Tools",
        "description": "Functions the LLM can invoke for structured problem-solving."
      },
      {
        "name": "Resources",
        "description": "Retrievable data entities for direct model use."
      },
      {
        "name": "Resource Templates",
        "description": "Predefined patterns for generating structured responses."
      },
      {
        "name": "Prompts",
        "description": "AI prompts guiding reasoning and decision-making."
      }
    ],
    "usage_instructions": "Leverage available tools, resources, templates, and prompts to enhance responses by retrieving data or executing structured actions."
  }
}
"""

initial_prompt_template = """
An MCP Server is defined as [{mcp_server_definition}],
These MCP Server(s) are available [{mcp_server_descriptions}],
Examine the user goal and propose calls to the MCP Server(s) to achieve the goal {goal}.
Respond only with valid JSON, without any additional text or explanations.
Where the JSON format for each required MCP Server call is:

```json
[
    {{
       "call_id": "unique identifier for the call",
       "mcp_server_name": "server name supplies in server descriptions",
       "mcp_capability": "tools|resources|resource_templates|prompts",
       "parameters": {{
          "parameter_name": "parameter_value"
       }}
    }}
]
"""

initial_prompt = PromptTemplate(
    input_variables=["mcp_server_definition",
                     "mcp_server_descriptions", "goal"],
    template=initial_prompt_template
)


def get_initial_prompt(mcp_server_descriptions: str,
                       goal: str) -> str:
    return initial_prompt.format(mcp_server_definition=mcp_server_definition,
                                 mcp_server_descriptions=mcp_server_descriptions,
                                 goal=goal)
