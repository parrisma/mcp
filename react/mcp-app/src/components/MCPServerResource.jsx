import React from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const MCPServerResource = ({ resource }) => {
  return (
    <Box
      sx={{ mb: 1, pl: 1, borderLeft: "2px solid #eee" }}
    >
      <Typography variant="body2" sx={{ fontWeight: "medium" }}>
        {resource.name}
      </Typography>
      <Typography
        variant="caption"
        color="text.secondary"
        component="div"
      >
        {resource.description}
      </Typography>
      <Typography
        variant="caption"
        component="div"
        sx={{ mt: 0.5, fontFamily: "monospace" }}
      >
        URI: {resource.uri}
      </Typography>
    </Box>
  );
};

export default MCPServerResource;