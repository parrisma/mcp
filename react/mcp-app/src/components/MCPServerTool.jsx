import React from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const MCPServerTool = ({ tool }) => {
  return (
    <Box
      sx={{ mb: 1, pl: 1, borderLeft: "2px solid #eee" }}
    >
      <Typography variant="body2" sx={{ fontWeight: "medium" }}>
        {tool.name}
      </Typography>
      <Typography
        variant="caption"
        color="text.secondary"
        component="div"
      >
        {tool.description}
      </Typography>
      {tool.inputSchema?.properties && (
        <Typography
          variant="caption"
          component="div"
          sx={{ mt: 0.5 }}
        >
          Arguments:{" "}
          {Object.keys(tool.inputSchema.properties).join(", ")}
        </Typography>
      )}
    </Box>
  );
};

export default MCPServerTool;