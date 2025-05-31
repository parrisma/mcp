import React, { useState } from "react";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button"; // Import Button
import PropTypes from "prop-types"; // For prop validation

function Prompt({
  baseApiUrl,
  onApiResponse,
  isNextStepsMode,
  onResetAll,
  sessionId,
  isLoading,
}) {
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
    onApiResponse(
      { data: null, loading: true, error: null },
      promptText,
      sessionId
    );

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
    label: "Enter Question & press [Submit]",
    placeholder:
      "Enter your question, and then press [submit]. If the model needs more information, it will suggest MCP actions and / or ask you for clarification questions. If it does this press [Do Next Steps] to proceed",
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
          disabled={isLoading || isNextStepsMode} // Only disable if loading or in next steps mode
        >
          {isLoading ? "Submitting..." : "Submit"}
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
            "&:hover .MuiOutlinedInput-notchedOutline": {
              borderColor: "rgba(0, 0, 0, 0.23)", // Keep border static on hover for readOnly
            },
          }}
          title="Session Id"
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
