import React, { useState, useEffect } from "react";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField"; // Import TextField
import PropTypes from "prop-types"; // Import PropTypes
import Typography from "@mui/material/Typography"; // Import Typography

function Questions({ clarifications, onResponsesChange }) {
  const [responses, setResponses] = useState([]);

  useEffect(() => {
    if (clarifications && Array.isArray(clarifications)) {
      setResponses(Array(clarifications.length).fill(""));
    } else {
      setResponses([]);
    }
  }, [clarifications]);

  const handleResponseChange = (index, value) => {
    const newResponses = [...responses];
    newResponses[index] = value;
    setResponses(newResponses);
    const structuredResponses = newResponses.map((response, i) => ({
      question: clarifications[i].question,
      response: response === "" ? "No user response" : response,
    }));
    if (onResponsesChange) {
      onResponsesChange(structuredResponses);
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 2,
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 1,
        padding: 2,
        maxHeight: "233px", // Set a max height
        overflowY: "auto", // Enable vertical scrolling
      }}
    >
      {/* Centered header */}
      <Typography
        variant="h6"
        component="div"
        sx={{ textAlign: "center", fontSize: "0.875rem" }}
      >
        {" "}
        {/* Added fontSize */}
        {clarifications &&
        Array.isArray(clarifications) &&
        clarifications.length > 0
          ? "Please respond to these questions"
          : "No Questions needing your clarification"}
      </Typography>
      {/* Dynamically add TextFields for each clarification question */}
      {clarifications &&
        Array.isArray(clarifications) &&
        clarifications.map((clarification, index) => (
          <Box key={index} sx={{ mb: 2 }}>
            {" "}
            {/* Wrap question and answer in a Box with bottom margin */}
            <Typography variant="caption" gutterBottom>
              {" "}
              {/* Display question as Typography */}
              {clarification.question}
            </Typography>
            <TextField
              variant="outlined"
              fullWidth
              placeholder="Enter your response here and it will be sent back to the LLM"
              value={responses[index] || ""}
              onChange={(e) => handleResponseChange(index, e.target.value)}
            />
          </Box>
        ))}
      {(!clarifications ||
        !Array.isArray(clarifications) ||
        clarifications.length === 0) && (
        <Box sx={{ textAlign: "center", color: "text.secondary" }}></Box>
      )}
    </Box>
  );
}

Questions.propTypes = {
  clarifications: PropTypes.arrayOf(
    PropTypes.shape({
      question: PropTypes.string.isRequired,
    })
  ),
  onResponsesChange: PropTypes.func,
};

Questions.defaultProps = {
  clarifications: [],
};

export default Questions;
