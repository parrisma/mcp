import React, { useState } from "react";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import PropTypes from "prop-types"; // For prop validation

function Prompt({ baseApiUrl, onApiResponse, isNextStepsMode, onResetAll }) {
  const [promptText, setPromptText] = useState("");
  const [isLoading, setIsLoading] = useState(false);

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

    setIsLoading(true);
    // Pass the promptText as the second argument to onApiResponse (handlePromptSubmitResponse in App.jsx)
    onApiResponse({ data: null, loading: true, error: null }, promptText);

    try {
      const fullUrl = `${baseApiUrl}/model_response?goal=${encodeURIComponent(
        promptText
      )}`;
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
      onApiResponse({ data: null, loading: false, error: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setPromptText(""); // Clear promptText locally on reset
    setIsLoading(false); // Ensure loading is also reset
    if (onResetAll) {
      onResetAll(); // This will clear apiStatus in App.jsx, making isNextStepsMode false
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
      <Box sx={{ display: "flex", justifyContent: "flex-start", gap: 1 }}> {/* Added gap for buttons */}
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
      </Box>
    </Box>
  );
}

Prompt.propTypes = {
  baseApiUrl: PropTypes.string,
  onApiResponse: PropTypes.func.isRequired,
  isNextStepsMode: PropTypes.bool,
  onResetAll: PropTypes.func.isRequired, // Add prop type for onResetAll
};

Prompt.defaultProps = {
  baseApiUrl: "",
  isNextStepsMode: false,
};

export default Prompt;
