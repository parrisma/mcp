import React, { useState, useEffect } from "react";
import TextField from "@mui/material/TextField";
import PropTypes from "prop-types";
import Box from "@mui/material/Box"; // For layout

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
function Status({ apiStatus, baseApiUrl, onApiResponse, lastResponseData }) {
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
    content = `thinking ${elapsedSeconds}s`;
  } else if (error) {
    content = `Error: ${error}`;
  } else if (data && data.response) { // Check for the nested 'response' object
    const responseData = data.response;
    if (responseData.answer && typeof responseData.answer.body !== 'undefined') {
      content = responseData.answer.body;
    } else if (responseData.mcp_server_calls && responseData.mcp_server_calls.length > 0) {
      content = `Pending MCP Server Calls:\n${JSON.stringify(responseData.mcp_server_calls, null, 2)}`;
    } else if (responseData.clarifications && responseData.clarifications.length > 0) {
      content = `Pending Clarifications:\n${JSON.stringify(responseData.clarifications, null, 2)}`;
    } else {
      // Fallback to stringifying the nested response object
      content = JSON.stringify(responseData, null, 2);
    }
  } else if (data) { // Fallback if data is not structured with 'data.response'
    content = JSON.stringify(data, null, 2);
  } else {
    content = "No response yet. Submit a prompt.";
  }

  // Correctly access thinking from data.response.thinking
  const thinkingData = data?.response?.thinking;
  const reasoningText = thinkingData?.reasoning || "";
  const nextStepsText = Array.isArray(thinkingData?.next_steps)
    ? (thinkingData.next_steps.join('\n') || "")
    : (thinkingData?.next_steps || "");

  const textFieldStyles = {
    "& .MuiInputBase-root": {
      fontFamily: "monospace",
      fontSize: "0.875rem",
      whiteSpace: "pre-wrap",
      wordBreak: "break-all",
    },
    "& .MuiInputBase-input": {
        userSelect: "text",
    },
    "&:hover .MuiOutlinedInput-notchedOutline": { // Keep border static on hover for readOnly
        borderColor: "rgba(0, 0, 0, 0.23)",
    },
  };

  const handleDoNextSteps = async () => {
    if (!baseApiUrl) {
      console.error("Base API URL is not provided to Status component for Next Steps.");
      onApiResponse({ data: null, loading: false, error: "Configuration error: Base API URL missing for Next Steps." });
      return;
    }
    if (!nextStepsText || nextStepsText.toLowerCase().trim() === "none") {
      onApiResponse({ data: null, loading: false, error: "No next steps to perform." });
      return;
    }

    setIsNextStepsLoading(true);
    // Use onApiResponse to signal loading, preserving existing data if appropriate
    // The App.jsx onApiResponse handler should manage startTime for this new loading sequence
    onApiResponse({ data: lastResponseData, loading: true, error: null });


    try {
      // Construct query parameters
      const params = new URLSearchParams();
      params.append("goal", nextStepsText);
      if (lastResponseData) {
        params.append("questions", JSON.stringify(lastResponseData));
      }
      
      const fullUrl = `${baseApiUrl}/model_response?${params.toString()}`;
      
      const response = await fetch(fullUrl);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: `HTTP error: ${response.status}` }));
        throw new Error(errorData.error || `HTTP error: ${response.status}`);
      }
      
      const responseData = await response.json();
      onApiResponse({ data: responseData, loading: false, error: null });
    } catch (err) {
      onApiResponse({ data: lastResponseData, loading: false, error: err.message });
    } finally {
      setIsNextStepsLoading(false);
    }
  };
  
  const canDoNextSteps = nextStepsText && nextStepsText.trim() !== "" && nextStepsText.toLowerCase().trim() !== "none";

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <TextField
        label="Response"
        multiline
        rows={10}
        value={content}
        variant="outlined"
        fullWidth
        readOnly={true}
        sx={textFieldStyles}
      />
      <TextField
        label="Reasoning"
        multiline
        rows={2}
        value={reasoningText}
        variant="outlined"
        fullWidth
        readOnly={true}
        sx={textFieldStyles}
      />
      <TextField
        label="Next Steps"
        multiline
        rows={2}
        value={nextStepsText}
        variant="outlined"
        fullWidth
        readOnly={true}
        sx={textFieldStyles}
      />
      <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
        <button
          onClick={handleDoNextSteps}
          disabled={!canDoNextSteps || loading || isNextStepsLoading}
          style={{
            padding: "4px 12px",
            borderRadius: 4,
            border: "1px solid #1976d2",
            background: (!canDoNextSteps || loading || isNextStepsLoading) ? "#ccc" : "#1976d2",
            color: "#fff",
            cursor: (!canDoNextSteps || loading || isNextStepsLoading) ? "not-allowed" : "pointer",
          }}
        >
          {isNextStepsLoading ? "Processing..." : "Do Next Steps"}
        </button>
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
};

export default Status;
