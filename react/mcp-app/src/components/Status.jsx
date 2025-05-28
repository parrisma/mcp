import React, { useState, useEffect } from "react";
import Typography from "@mui/material/Typography";
import PropTypes from "prop-types";
import CircularProgress from "@mui/material/CircularProgress"; // For loading state
import Box from "@mui/material/Box"; // For centering loader

/**
 * Status component to display API call status and response.
 * @param {object} props - The component's props.
 * @param {object} props.apiStatus - The status of the API call.
 * @param {object} props.apiStatus.data - The response data.
 * @param {boolean} props.apiStatus.loading - Loading state.
 * @param {string|null} props.apiStatus.error - Error message.
 * @param {number|null} props.apiStatus.startTime - Timestamp when loading started.
 * @returns {JSX.Element}
 */
function Status({ apiStatus }) {
  const { data, loading, error, startTime } = apiStatus || {};
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

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
    content = (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100%",
          flexDirection: "column", // Stack spinner and text vertically
        }}
      >
        <CircularProgress />
        <Typography sx={{ mt: 2 }}>
          Processing your request... (Elapsed: {elapsedSeconds}s)
        </Typography>
      </Box>
    );
  } else if (error) {
    content = <Typography color="error">Error: {error}</Typography>;
  } else if (data) {
    // Assuming data is an object that needs to be stringified
    content = JSON.stringify(data, null, 2);
  } else {
    content = "No response yet. Submit a prompt.";
  }

  return (
    <Typography
      component="pre"
      data-testid="status-message"
      sx={{
        border: 1,
        borderRadius: 1,
        p: 2,
        minHeight: "200px", // Ensure a minimum height
        height: "auto", // Allow height to grow
        maxHeight: "400px", // But also have a max height with scroll
        overflowY: "auto",
        whiteSpace: "pre-wrap",
        wordBreak: "break-word",
        userSelect: "text",
        fontFamily: "monospace", // Good for JSON
        fontSize: "0.875rem",
      }}
      tabIndex={0}
      aria-readonly="true"
    >
      {content}
    </Typography>
  );
}

Status.propTypes = {
  apiStatus: PropTypes.shape({
    data: PropTypes.any,
    loading: PropTypes.bool,
    error: PropTypes.string,
    startTime: PropTypes.number, // Add startTime to propTypes
  }),
};

Status.defaultProps = {
  apiStatus: {
    data: null,
    loading: false,
    error: null,
    startTime: null, // Add startTime to defaultProps
  },
};

export default Status;
