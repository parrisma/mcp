import React from "react";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField"; // Import TextField
import PropTypes from "prop-types"; // Import PropTypes
import Typography from "@mui/material/Typography"; // Import Typography

function Questions({ clarifications }) {
  // Accept clarifications prop
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
        Questions needing your clarification
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
              // You might want to add state here later to capture user input
            />
          </Box>
        ))}
      {(!clarifications ||
        !Array.isArray(clarifications) ||
        clarifications.length === 0) && (
        <Box sx={{ textAlign: "center", color: "text.secondary" }}>
          No clarification questions.
        </Box>
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
};

Questions.defaultProps = {
  clarifications: [],
};

export default Questions;
