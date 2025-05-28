import React, { useState } from "react";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";

function Prompt() {
  const [promptText, setPromptText] = useState("");

  const handleInputChange = (event) => {
    setPromptText(event.target.value);
  };

  const handleSubmit = () => {
    // Handle submission logic here
    console.log("Submitted prompt:", promptText);
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
      <TextField {...promptProps} onChange={handleInputChange} />
      <Box sx={{ display: "flex", justifyContent: "flex-start" }}>
        <Button variant="contained" color="primary" onClick={handleSubmit}>
          Submit
        </Button>
      </Box>
    </Box>
  );
}

export default Prompt;
