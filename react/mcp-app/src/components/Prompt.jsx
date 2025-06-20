import React, { useState, useEffect } from "react";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button"; // Import Button
import PropTypes from "prop-types"; // For prop validation

function Prompt({
  baseApiUrl,
  onApiResponse,
  onResetAll,
  sessionId,
  isLoading,
  activityStatus, // Add new prop for activity status
  isFinalAnswerContentDisplayed, // Add new prop
  promptText, // Add promptText prop
  setPromptText, // Add setPromptText prop
}) {
  const [activityText, setActivityText] = useState(""); // State for Activity TextField

  // Update activityText when activityStatus prop changes
  useEffect(() => {
    if (activityStatus) {
      setActivityText(activityStatus);
    } else {
      setActivityText("");
    }
  }, [activityStatus]);

  const handleInputChange = (event) => {
    setPromptText(event.target.value);
  };

  const handleSubmit = async () => {
    if (isLoading) {
      // Prevent double submission
      return;
    }
    if (!baseApiUrl) {
      onApiResponse({
        data: null,
        loading: false,
        error: "Configuration error: Base API URL missing.",
      });
      return;
    }
    if (!promptText.trim()) {
      onApiResponse({
        data: null,
        loading: false,
        error: "Prompt cannot be empty.",
      });
      return;
    }

    // Pass the promptText and the current sessionId up to App.jsx
    // App.jsx will manage the loading state
    onApiResponse(
      { data: null, loading: true, error: null },
      promptText, // Use the prop
      sessionId
    );

    // The actual API call will be made in App.jsx after sessionId is updated
  };

  const handleReset = () => {
    setPromptText(""); // Clear promptText using the prop
    // App.jsx will manage the loading state reset via onResetAll
    if (onResetAll) {
      onResetAll(); // This will clear apiStatus in App.jsx, making isNextStepsMode false and loading false
    }
  };

  const promptProps = {
    id: "prompt-textfield",
    label: "Enter Question & press [Submit]",
    placeholder:
      "Enter your question, and then press [submit]. If the model needs more information, it will suggest MCP actions and / or ask you for clarification questions. If it does this press [Do Next Steps] to proceed",
    multiline: true,
    rows: 11,
    value: promptText, // Use the prop
    variant: "outlined",
    fullWidth: true,
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <TextField
        {...promptProps}
        onChange={handleInputChange}
        disabled={isLoading}
      />
      <Box
        sx={{
          display: "flex",
          justifyContent: "flex-start",
          gap: 1,
          alignItems: "center",
        }}
      >
        {" "}
        {/* Added gap for buttons and alignment */}
        <Button
          variant="contained" // Use contained variant
          onClick={handleSubmit}
          disabled={isLoading || isFinalAnswerContentDisplayed} // Disable when loading or when final answer content is displayed
        >
          {isFinalAnswerContentDisplayed
            ? "Done"
            : isLoading
            ? "Submitting..."
            : "Submit"}
        </Button>
        <Button
          variant="contained" // Use contained variant
          onClick={handleReset}
        >
          Reset
        </Button>
        <TextField
          label="Session ID"
          value={sessionId}
          variant="outlined"
          size="small"
          InputProps={{
            readOnly: true,
            sx: {
              fontFamily: "monospace", // Override font to monospace
            },
          }}
          sx={{
            width: "350px", // Adjust width as needed
            "& .MuiInputBase-root": {
              fontSize: "0.875rem", // Smaller font size for Session ID
              fontFamily: "monospace", // Ensure monospace font for input
            },
          }}
          title="Session Id"
        />
        <TextField
          label="Activity"
          value={activityText}
          variant="outlined"
          size="small"
          InputProps={{
            readOnly: true,
            sx: {
              fontFamily: "monospace", // Override font to monospace
            },
          }}
          sx={{
            flexGrow: 1, // Allow the field to grow and take available space
            "& .MuiInputBase-root": {
              fontSize: "0.875rem", // Smaller font size for Activity
              fontFamily: "monospace", // Ensure monospace font for input
            },
          }}
          title="Current Activity"
        />
      </Box>
    </Box>
  );
}

Prompt.propTypes = {
  baseApiUrl: PropTypes.string,
  onApiResponse: PropTypes.func.isRequired,
  onResetAll: PropTypes.func.isRequired, // Add prop type for onResetAll
  sessionId: PropTypes.string, // Add prop type for sessionId
  isLoading: PropTypes.bool, // Add prop type for isLoading
  activityStatus: PropTypes.string, // Add prop type for activityStatus
  isFinalAnswerDisplayed: PropTypes.bool, // Add prop type
  isFinalAnswerContentDisplayed: PropTypes.bool, // Add new prop type
  promptText: PropTypes.string.isRequired, // Add prop type for promptText
  setPromptText: PropTypes.func.isRequired, // Add prop type for setPromptText
};

Prompt.defaultProps = {
  baseApiUrl: "",
  sessionId: null, // Default prop for sessionId
  isLoading: false, // Default prop for isLoading
  activityStatus: "", // Default prop for activityStatus
  isFinalAnswerContentDisplayed: false, // Add new default prop
  promptText: "", // Default prop for promptText
  setPromptText: () => {}, // Default prop for setPromptText
};

export default Prompt;
