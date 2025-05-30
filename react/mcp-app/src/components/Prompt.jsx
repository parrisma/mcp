import React, { useState } from "react";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import PropTypes from "prop-types"; // For prop validation

function Prompt({ baseApiUrl, onApiResponse, isNextStepsMode, onResetAll, sessionId, isLoading }) {
  const [promptText, setPromptText] = useState("");

  const handleInputChange = (event) => {
    setPromptText(event.target.value);
  };

  const handleSubmit = async () => {
    if (!baseApiUrl) {
      console.error("Base API URL is not provided to Prompt component.");
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
    onApiResponse({ data: null, loading: true, error: null }, promptText, sessionId);

    // The actual API call will be made in App.jsx after sessionId is updated
  };

  const handleReset = () => {
    setPromptText(""); // Clear promptText locally on reset
    // App.jsx will manage the loading state reset via onResetAll
    if (onResetAll) {
      onResetAll(); // This will clear apiStatus in App.jsx, making isNextStepsMode false and loading false
    }
  };

  const promptProps = {
    id: "prompt-textfield",
    label: "Enter your question",
    multiline: true,
    rows: 10,
    value: promptText,
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
      <Box sx={{ display: "flex", justifyContent: "flex-start", gap: 1, alignItems: 'center' }}> {/* Added gap for buttons and alignment */}
        <button
          onClick={handleSubmit}
          disabled={isLoading || isNextStepsMode} // Only disable if loading or in next steps mode
          style={{
            padding: "4px 12px",
            borderRadius: 4,
            border: "1px solid #1976d2",
            background: (isLoading || isNextStepsMode) ? "#ccc" : "#1976d2", // Background changes if disabled
            color: "#fff",
            cursor: (isLoading || isNextStepsMode) ? "not-allowed" : "pointer",
          }}
        >
          {isLoading ? "Submitting..." : "Submit"}
        </button>
        <button
          onClick={handleReset}
          style={{
            padding: "4px 12px",
            borderRadius: 4,
            border: "1px solid #1976d2",
            background: "#1976d2", // Same blue as Submit
            color: "#fff",
            cursor: "pointer",
          }}
        >
          Reset
        </button>
        <TextField
          label="Session ID"
          value={sessionId}
          variant="outlined"
          size="small"
          readOnly={true}
          sx={{
            width: '280px', // Adjust width as needed
            "& .MuiInputBase-root": {
              fontSize: "0.75rem", // Smaller font size for Session ID
            },
            "&:hover .MuiOutlinedInput-notchedOutline": {
              borderColor: "rgba(0, 0, 0, 0.23)", // Keep border static on hover for readOnly
            },
          }}
        />
      </Box>
    </Box>
  );
}

Prompt.propTypes = {
  baseApiUrl: PropTypes.string,
  onApiResponse: PropTypes.func.isRequired,
  isNextStepsMode: PropTypes.bool,
  onResetAll: PropTypes.func.isRequired, // Add prop type for onResetAll
  sessionId: PropTypes.string, // Add prop type for sessionId
  isLoading: PropTypes.bool, // Add prop type for isLoading
};

Prompt.defaultProps = {
  baseApiUrl: "",
  isNextStepsMode: false,
  sessionId: null, // Default prop for sessionId
  isLoading: false, // Default prop for isLoading
};

export default Prompt;
