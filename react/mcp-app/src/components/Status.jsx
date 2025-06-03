import React, { useState, useEffect } from "react";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button"; // Import Button
import PropTypes from "prop-types";
import Box from "@mui/material/Box"; // For layout
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
  baseApiUrl,
  onApiResponse,
  lastResponseData,
  currentGoalPromptText,
  sessionId,
  onClarificationResponsesChange, // Accept the new prop
}) {
  const { data, loading, error, startTime } = apiStatus || {};
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [isNextStepsLoading, setIsNextStepsLoading] = useState(false);
  const [clarificationResponses, setClarificationResponses] = useState([]); // State to hold responses from Questions

  useEffect(() => {
    let intervalId;
    if (loading && startTime) {
      setElapsedSeconds(Math.floor((Date.now() - startTime) / 1000)); // Initial calculation
      intervalId = setInterval(() => {
        setElapsedSeconds(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);
    } else {
      setElapsedSeconds(0); // Reset when not loading or no startTime
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [loading, startTime]);

  // Pass clarification responses up to the parent whenever they change
  useEffect(() => {
    if (onClarificationResponsesChange) {
      onClarificationResponsesChange(clarificationResponses);
    }
  }, [clarificationResponses, onClarificationResponsesChange]);


  let content;

  if (error) {
    content = `Error: ${error}`;
  } else if (data && data.response) {
    // Check for the nested 'response' object
    const responseData = data.response;
    if (responseData.answer) {
      // Display the answer if available
      if (typeof responseData.answer === 'object' && responseData.answer !== null && responseData.answer.body !== undefined && responseData.answer.confidence !== undefined) {
        content = `${responseData.answer.body} with confidence ${responseData.answer.confidence}`;
      } else if (typeof responseData.answer === 'object' && responseData.answer !== null) {
        content = JSON.stringify(responseData.answer, null, 2);
      }
       else {
        content = responseData.answer;
      }
    } else if (
      responseData.mcp_server_calls &&
      responseData.mcp_server_calls.length > 0
    ) {
      // Otherwise, show MCP server calls if present
      content = `Pending MCP Server Calls:\n${JSON.stringify(
        responseData.mcp_server_calls,
        null,
        2
      )}`;
    } else {
      // Default content if no answer or MCP calls
      content = "";
    }
  } else {
    // Default content when no data or response
    content = "";
  }

  // Correctly access thinking from data.response.thinking
  const thinkingData = data?.response?.thinking;
  const reasoningText = thinkingData?.reasoning || "";
  const nextStepsText = Array.isArray(thinkingData?.next_steps)
    ? thinkingData.next_steps.join("\n") || ""
    : thinkingData?.next_steps || "";

  const handleDoNextSteps = async () => {
    if (!baseApiUrl) {
      console.error(
        "Base API URL is not provided to Status component for Next Steps."
      );
      onApiResponse({
        data: null,
        loading: false,
        error: "Configuration error: Base API URL missing for Next Steps.",
      });
      return;
    }
    if (!nextStepsText || nextStepsText.toLowerCase().trim() === "none") {
      onApiResponse({
        data: null,
        loading: false,
        error: "No next steps to perform.",
      });
      return;
    }

    setIsNextStepsLoading(true);
    // Use onApiResponse to signal loading, preserving existing data if appropriate
    // The App.jsx onApiResponse handler should manage startTime for this new loading sequence
    onApiResponse({ data: lastResponseData, loading: true, error: null });

    try {
      // Construct query parameters
      const params = new URLSearchParams();
      params.append("goal", currentGoalPromptText); // Use the original prompt text as the goal

      // Include clarification responses in the 'questions' parameter
      // Create a deep copy of lastResponseData to avoid modifying the original state directly
      const questionsData = JSON.parse(JSON.stringify(lastResponseData));
      
      // Update the clarifications within the nested 'response' object
      if (questionsData && questionsData.response) {
        questionsData.response.clarifications = clarificationResponses;
      } else {
        // Handle cases where response or clarifications might be missing initially
        questionsData.response = { clarifications: clarificationResponses };
      }

      params.append("questions", JSON.stringify(questionsData));

      // Add the session id to the parameters
      params.append("session", sessionId);

      const fullUrl = `${baseApiUrl}/model_response?${params.toString()}`;

      const response = await fetch(fullUrl);

      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ error: `HTTP error: ${response.status}` }));
        throw new Error(errorData.error || `HTTP error: ${response.status}`);
      }

      const responseData = await response.json();
      onApiResponse({ data: responseData, loading: false, error: null });
    } catch (err) {
      onApiResponse({
        data: lastResponseData,
        loading: false,
        error: err.message,
      });
    } finally {
      setIsNextStepsLoading(false);
    }
  };

  const canDoNextSteps =
    nextStepsText &&
    nextStepsText.trim() !== "" &&
    nextStepsText.toLowerCase().trim() !== "none";

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box  mb={2} sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}> {/* Changed to 2fr 1fr */}
        {/* First column: the main TextField */}
        <TextField
          label={data?.response?.answer ? "Answer" : "(MCP) Requested Actions"}
          multiline
          rows={10}
          value={content}
          variant="outlined"
          fullWidth
          readOnly={true}
          sx={{
            '& .MuiOutlinedInput-root': {
              '& fieldset': {
                borderColor: error ? 'red' : (data?.response?.answer ? 'green' : undefined),
              },
              '&:hover fieldset': {
                borderColor: error ? 'red' : (data?.response?.answer ? 'green' : undefined),
              },
              '&.Mui-focused fieldset': {
                borderColor: error ? 'red' : (data?.response?.answer ? 'green' : undefined),
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
      <Box mb={2}> {/* Added margin bottom */}
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
      <Box mb={2}> {/* Added margin bottom */}
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
      <Box sx={{ display: "flex", justifyContent: "flex-start" }} mb={2}> {/* Added margin bottom */}
        <Button
          variant="contained" // Use contained variant for a filled button
          onClick={handleDoNextSteps}
          disabled={
            !canDoNextSteps ||
            loading ||
            isNextStepsLoading ||
            data?.response?.answer?.body !== undefined
          }
        >
          {isNextStepsLoading ? "Processing..." : "Do Next Steps"}
        </Button>
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
