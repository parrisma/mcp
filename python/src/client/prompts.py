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

llm_prompt_template = """
Examine and respond to the goal, between >> and <<
>>
{goal}
<<
you can do **ONE* of
1. use MCP Servers defined as [{mcp_server_definition}], where these MCP Server(s) are available [{mcp_server_descriptions}]
2. ask questions to clarify the goal.
3. provide a final response when you have enough information, where a valid response is to decline where the scope of goal is outside the MCP Server(s) capabilities.

MCP Server call responses you have asked to run will be here as JSON
```json
{{
    {mcp_server_responses}
}}
```

Question responses you have asked to clarify about the goal will be here as JSON
```json
{{
    {clarification_responses}
}}
```

Your response must be valid, strictly formatted JSON that adheres to the following rules:
- ONLY ONE of the following response types:
- Type 1. MCP Calls → Execute an MCP action with the provided parameters.
- Type 2. Clarifications → Ask for additional details before proceeding.
- Type 3. Final Response → Provide an answer only when sufficient information is available.
- No mixed responses → Do not combine multiple response types in the same JSON output.
- Strict JSON compliance → The output must be correctly formatted, parsable by any standard JSON library without modification. No additional in-line text, commentary, or explanation
- Important: If a computation requires multiple dependent operations, only return the first independent call. Do not chain calls that rely on unresolved outputs.
- If additional calls are required after a previous response, you will receive a follow-up prompt, with the answers passed to you in the same format as this prompt.
- *ALWAYS* include your reasoning and next steps, if there are no next steps just reply with "None".
- The JSON response must follow this structure,
```json
{{
  "mcp_server_calls": [
    {{
       "mcp_server_name": "server name supplies in server descriptions",
       "mcp_capability": "tools|resources|resource_templates|prompts",
       "mcp_capability_name": "name of the capability",
       "parameters": {{
          "parameter_name": "parameter_value"
       }}
    }}
  ],
  "clarifications": [
    {{
      "question": "point of clarification needed to respond to the goal"
    }}
  ],
  "answer": {{
    "body": "*FINAL* response *ONLY* when all  MCP calls and clarifications have been satisfied.",
    "confidence": "A % that reflects confidence in the response"
  }},
  "thinking": {{
    "reasoning": "The reasoning behind the MCP calls and clarifications requested, including any dependencies between them.",
    "next_steps": "The next steps to take based on the MCP calls and clarifications, if any."
  }}
}}
"""

initial_prompt = PromptTemplate(
    input_variables=["mcp_server_definition",
                     "mcp_server_descriptions", "goal"],
    template=llm_prompt_template
)


def get_llm_prompt(mcp_server_descriptions: str,
                   mcp_responses: str,
                   clarifications: str,
                   goal: str) -> str:
    return initial_prompt.format(mcp_server_definition=mcp_server_definition,
                                 mcp_server_descriptions=mcp_server_descriptions,
                                 mcp_server_responses=mcp_responses,
                                 clarification_responses=clarifications,
                                 goal=goal)
