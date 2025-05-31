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
 * @returns {JSX.Element}
 */
function Status({
  apiStatus,
  baseApiUrl,
  onApiResponse,
  lastResponseData,
  currentGoalPromptText,
  sessionId,
}) {
  const { data, loading, error, startTime } = apiStatus || {};
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [isNextStepsLoading, setIsNextStepsLoading] = useState(false);

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

  let content;

  if (loading) {
    content = `thinking, please be patient [${elapsedSeconds}s]`;
  } else if (error) {
    content = `Error: ${error}`;
  } else if (data && data.response) {
    // Check for the nested 'response' object
    const responseData = data.response;
    if (
      responseData.mcp_server_calls &&
      responseData.mcp_server_calls.length > 0
    ) {
      // Only show MCP server calls if present
      content = `Pending MCP Server Calls:\n${JSON.stringify(
        responseData.mcp_server_calls,
        null,
        2
      )}`;
    } else {
      // Otherwise, content is empty
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

      if (lastResponseData) {
        // Send the full lastResponseData object as the 'questions' parameter
        params.append("questions", JSON.stringify(lastResponseData));
      }
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
          label={data?.response?.answer ? "Answer" : "(MCP) Actions"}
          multiline
          rows={10}
          value={content}
          variant="outlined"
          fullWidth
          readOnly={true}
        />
        {
          /* Second column: */
          <Questions
            clarifications={data?.response?.clarifications}
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
};

export default Status;
