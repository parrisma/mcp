import React, { useState } from "react";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import PropTypes from "prop-types"; // For prop validation

function Prompt({ baseApiUrl, onApiResponse }) {
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
    onApiResponse({ data: null, loading: true, error: null });

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
      <Box sx={{ display: "flex", justifyContent: "flex-start" }}>
        <button
          onClick={handleSubmit}
          disabled={isLoading || !promptText.trim()}
          style={{
            padding: "4px 12px",
            borderRadius: 4,
            border: "1px solid #1976d2",
            background: isLoading || !promptText.trim() ? "#ccc" : "#1976d2", // Disabled style
            color: "#fff",
            cursor: isLoading || !promptText.trim() ? "not-allowed" : "pointer",
          }}
        >
          {isLoading ? "Submitting..." : "Submit"}
        </button>
      </Box>
    </Box>
  );
}

Prompt.propTypes = {
  baseApiUrl: PropTypes.string,
  onApiResponse: PropTypes.func.isRequired,
};

Prompt.defaultProps = {
  baseApiUrl: "",
};

export default Prompt;
