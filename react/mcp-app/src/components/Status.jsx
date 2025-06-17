import React, { useState, useEffect } from "react";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button"; // Import Button
import PropTypes from "prop-types";
import Box from "@mui/material/Box"; // For layout
import Typography from "@mui/material/Typography"; // Import Typography
import MuiMarkdown from 'mui-markdown'; // Import MuiMarkdown
import Questions from "./Questions"; // Import Questions component

/**
 * Status component to display API call status, response, reasoning, and next steps.
 * @param {object} props - The component's props.
 * @param {object} props.apiStatus - The status of the API call.
 * @param {object} props.apiStatus.data - The response data.
 * @param {boolean} props.apiStatus.loading - Loading state.
 * @param {string|null} props.apiStatus.error - Error message.
 * @param {number|null} props.apiStatus.startTime - Timestamp when loading started.
 * @param {function} props.onApiResponse - Callback function to update API status in parent.
 * @param {object|null} props.lastResponseData - The last received API response data.
 * @param {string} props.currentGoalPromptText - The original goal prompt text.
 * @param {string} props.sessionId - The current session ID.
 * @param {function} props.onClarificationResponsesChange - Callback function to pass clarification responses to parent.
 * @returns {JSX.Element}
 */
function Status({
  apiStatus,
  onClarificationResponsesChange, // Accept the new prop
}) {
  const { data, error } = apiStatus || {};
  const [clarificationResponses, setClarificationResponses] = useState([]); // State to hold responses from Questions

  // Pass clarification responses up to the parent whenever they change
  useEffect(() => {
    if (onClarificationResponsesChange) {
      onClarificationResponsesChange(clarificationResponses);
    }
  }, [clarificationResponses, onClarificationResponsesChange]);

  let requestedActionsContent;
  let finalAnswerContent = "";

  if (error) {
    requestedActionsContent = `Error: ${error}`;
  } else if (data && data.response) {
    // Check for the nested 'response' object
    const responseData = data.response;

    // Populate finalAnswerContent if answer is available
    if (responseData.answer) {
      if (
        typeof responseData.answer === "object" &&
        responseData.answer !== null &&
        responseData.answer.body !== undefined
      ) {
        let bodyContent = responseData.answer.body;
        if (typeof bodyContent === "object" && bodyContent !== null) {
          finalAnswerContent = JSON.stringify(bodyContent, null, 2);
        } else {
          finalAnswerContent = bodyContent;
        }
      } else if (responseData.answer !== undefined) {
        // If answer exists but is not an object with a body, display it directly
        finalAnswerContent = responseData.answer;
      }
    }

    // Populate requestedActionsContent with MCP server calls if present and no final answer
    if (
      !responseData.answer && // Only show requested actions if no final answer
      responseData.mcp_server_calls &&
      responseData.mcp_server_calls.length > 0
    ) {
      requestedActionsContent = `Pending MCP Server Calls:\n${JSON.stringify(
        responseData.mcp_server_calls,
        null,
        2
      )}`;
    } else if (!responseData.answer) {
       // If no answer and no MCP calls, requestedActionsContent is empty
       requestedActionsContent = "";
    } else {
      // If there is a final answer, requestedActionsContent should be empty
      requestedActionsContent = "";
    }

  } else {
    // Default content when no data or response
    requestedActionsContent = "";
  }

  // Correctly access thinking from data.response.thinking
  const thinkingData = data?.response?.thinking;
  const reasoningText = thinkingData?.reasoning || "";
  const nextStepsText = Array.isArray(thinkingData?.next_steps)
    ? thinkingData.next_steps.join("\n") || ""
    : thinkingData?.next_steps || "";

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box
        mb={2}
        sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}
      >
        {" "}
        {/* Changed to 2fr 1fr */}
        {/* First column: the main TextField */}
        <TextField
          label="(MCP) Requested Actions" // Always display this label
          multiline
          rows={10}
          value={requestedActionsContent} // Use the new variable
          variant="outlined"
          fullWidth
          readOnly={true}
          sx={{
            "& .MuiOutlinedInput-root": {
              "& fieldset": {
                borderColor: error ? "red" : undefined, // Only red border on error
              },
              "&:hover fieldset": {
                borderColor: error ? "red" : undefined, // Only red border on error
              },
              "&.Mui-focused fieldset": {
                borderColor: error ? "red" : undefined, // Only red border on error
              },
            },
          }}
        />
        {
          /* Second column: */
          <Questions
            clarifications={data?.response?.clarifications}
            onResponsesChange={setClarificationResponses} // Pass the setter to Questions
          />
        }
      </Box>
      {/* The rest of the fields below the grid */}
      {/* Final Answer TextField or Markdown Display */}
      <Box mb={2}>
        {(typeof finalAnswerContent === 'string' && finalAnswerContent.startsWith("markdown\n")) ? (
          <Box>
            <Typography
              variant="caption"
              component="div" // Using div for the label container
              sx={{
                fontSize: '0.75rem',
                color: 'text.secondary', // Use theme color for standard label grey
                mb: 0.5, // Spacing between label and markdown box
                pl: '14px', // Align with TextField label
                pt: '6px' // Align with TextField label
              }}
            >
              Final Answer
            </Typography>
            <Box
              sx={{
                p: "16.5px 14px",
                border: "1px solid",
                borderColor: data?.response?.answer ? "green" : "rgba(0, 0, 0, 0.23)",
                borderRadius: 1,
                height: `calc(1.4375em * 10 + ${16.5 * 2}px)`, // Approx 10 rows, fixed height
                overflowY: 'auto',
                overflowX: 'auto', // Add horizontal scrolling
                backgroundColor: 'rgba(0, 0, 0, 0.04)', // Mimic readOnly TextField background
                '&:hover': {
                  borderColor: data?.response?.answer ? "green" : "rgba(0, 0, 0, 0.87)",
                },
              }}
            >
              <MuiMarkdown>{finalAnswerContent.substring("markdown\n".length)}</MuiMarkdown>
            </Box>
          </Box>
        ) : (
          <TextField
              label="Final Answer"
              multiline
              rows={10}
              value={finalAnswerContent}
              variant="outlined"
              fullWidth
              InputProps={{ // Standard way to set readOnly for MUI v5+
                readOnly: true,
              }}
              sx={{
                "& .MuiOutlinedInput-root": {
                  "& fieldset": {
                    borderColor: data?.response?.answer ? "green" : undefined,
                  },
                  "&:hover fieldset": {
                    borderColor: data?.response?.answer ? "green" : undefined,
                  },
                  "&.Mui-focused fieldset": {
                    borderColor: data?.response?.answer ? "green" : undefined,
                  },
                  // If you want to ensure the background color for readOnly state:
                  // "&.Mui-disabled, .MuiInputBase-inputAdornedStart.Mui-disabled": {
                  //   backgroundColor: 'rgba(0, 0, 0, 0.04)',
                  // },
                },
              }}
            />
        )}
        </Box>
      <Box mb={2}>
        {" "}
        {/* Added margin bottom */}
        <TextField
          label="Reasoning"
          multiline
          rows={2}
          value={reasoningText}
          variant="outlined"
          fullWidth
          readOnly={true}
        />
      </Box>
      <Box mb={2}>
        {" "}
        {/* Added margin bottom */}
        <TextField
          label="Next Steps"
          multiline
          rows={2}
          value={nextStepsText}
          variant="outlined"
          fullWidth
          readOnly={true}
        />
      </Box>
      <Box sx={{ display: "flex", justifyContent: "flex-start" }} mb={2}>
        {" "}
        {/* Added margin bottom */}
      </Box>
    </Box>
  );
}

Status.propTypes = {
  apiStatus: PropTypes.shape({
    data: PropTypes.any,
    loading: PropTypes.bool,
    error: PropTypes.string,
    startTime: PropTypes.number,
  }),
  baseApiUrl: PropTypes.string,
  onApiResponse: PropTypes.func.isRequired,
  lastResponseData: PropTypes.any,
  currentGoalPromptText: PropTypes.string, // Add prop type
  sessionId: PropTypes.string, // Add prop type for sessionId
  onClarificationResponsesChange: PropTypes.func, // Add prop type for the new prop
  onResetAll: PropTypes.func, // Add prop type for onResetAll
};

Status.defaultProps = {
  apiStatus: {
    data: null,
    loading: false,
    error: null,
    startTime: null,
  },
  baseApiUrl: "",
  lastResponseData: null,
  currentGoalPromptText: "", // Add default prop
  sessionId: null, // Add default prop for sessionId
  onClarificationResponsesChange: null, // Add default prop for the new prop
  onResetAll: null, // Add default prop for onResetAll
};

export default Status;
