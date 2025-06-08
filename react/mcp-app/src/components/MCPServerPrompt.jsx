import React from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const MCPServerPrompt = ({ prompt }) => {
  return (
    <Box
      sx={{ mb: 1, pl: 1, borderLeft: "2px solid #eee" }}
    >
      <Typography variant="body2" sx={{ fontWeight: "medium" }}>
        {prompt.name}
      </Typography>
      <Typography
        variant="caption"
        color="text.secondary"
        component="div"
      >
        {prompt.description}
      </Typography>
      {prompt.arguments &&
        Array.isArray(prompt.arguments) &&
        prompt.arguments.length > 0 && (
          <Box sx={{ mt: 0.5, pl: 1 }}>
            <Typography
              variant="caption"
              sx={{ fontWeight: "medium" }}
            >
              Arguments:
            </Typography>
            {prompt.arguments.map((arg, argIndex) => (
              <Box key={argIndex} sx={{ pl: 1 }}>
                <Typography variant="caption" component="div">
                  <strong>{arg.name}</strong> (
                  {arg.required ? "required" : "optional"}):{" "}
                  {arg.description}
                </Typography>
              </Box>
            ))}
          </Box>
        )}
    </Box>
  );
};

export default MCPServerPrompt;