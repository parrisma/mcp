import React from "react";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Divider from "@mui/material/Divider";
import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import MCPServerTool from "./MCPServerTool";
import MCPServerResource from "./MCPServerResource";
import MCPServerResourceTemplate from "./MCPServerResourceTemplate";
import MCPServerPrompt from "./MCPServerPrompt";

const textFieldSx = {
  width: "100%",
  "& .MuiInputBase-input": {
    color: "#757575",
    fontSize: "0.875rem",
  },
  "&:hover .MuiOutlinedInput-notchedOutline": {
    borderColor: "rgba(0, 0, 0, 0.23)",
  },
  "& .MuiInputLabel-root": {
    // Ensure label size is also consistent
    fontSize: "0.875rem",
  },
};

const MCPServerCard = ({ jsonData, title }) => {
  if (!jsonData) {
    return (
      <Card variant="outlined">
        <CardContent>
          <Typography color="text.secondary">No data provided.</Typography>
        </CardContent>
      </Card>
    );
  }

  let displayData = jsonData;
  let cardTitle = title;

  // If jsonData is an object with a single top-level key,
  // use that key as the title and its value as the data to display.
  if (
    typeof jsonData === "object" &&
    jsonData !== null &&
    Object.keys(jsonData).length === 1 &&
    !title // Only override if no explicit title is given
  ) {
    cardTitle = Object.keys(jsonData)[0];
    displayData = jsonData[cardTitle];
  }

  const serverDetail = displayData?.server_detail;
  const tools = displayData?.tools;
  const resources = displayData?.resources;
  const resourceTemplates = displayData?.resource_templates;
  const prompts = displayData?.prompts;
  const prettyJson = JSON.stringify(displayData, null, 2);

  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      {cardTitle && (
        <Box sx={{ p: 2, borderBottom: "1px solid rgba(0, 0, 0, 0.12)" }}>
          <Typography variant="h6" component="div">
            {cardTitle}
          </Typography>
        </Box>
      )}
      <CardContent>
        {serverDetail && (
          <Box sx={{ mb: 2 }}>
            <Typography
              variant="subtitle1"
              gutterBottom
              component="div"
              sx={{ fontWeight: "bold" }}
            >
              Server Detail
            </Typography>
            <TextField
              label="Name"
              value={serverDetail.name || ""}
              size="small"
              variant="outlined"
              readOnly
              sx={textFieldSx}
              margin="dense"
            />
            <TextField
              label="Instructions"
              value={serverDetail.instructions || ""}
              size="small"
              variant="outlined"
              readOnly
              multiline
              maxRows={4}
              sx={textFieldSx}
              margin="dense"
            />
            <TextField
              label="URL"
              value={serverDetail.server_url || ""}
              size="small"
              variant="outlined"
              readOnly
              sx={textFieldSx}
              margin="dense"
            />
            <TextField
              label="Version"
              value={serverDetail.version || ""}
              size="small"
              variant="outlined"
              readOnly
              sx={textFieldSx}
              margin="dense"
            />
            <Divider sx={{ my: 2 }} />
          </Box>
        )}
        {tools && Array.isArray(tools) && tools.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography
              variant="subtitle1"
              gutterBottom
              component="div"
              sx={{ fontWeight: "bold" }}
            >
              Tools
            </Typography>
            {tools.map((tool, index) => (
              <MCPServerTool key={index} tool={tool} />
            ))}
            <Divider sx={{ my: 2 }} />
          </Box>
        )}
        {resources && Array.isArray(resources) && resources.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography
              variant="subtitle1"
              gutterBottom
              component="div"
              sx={{ fontWeight: "bold" }}
            >
              Resources
            </Typography>
            {resources.map((resource, index) => (
              <MCPServerResource key={index} resource={resource} />
            ))}
            <Divider sx={{ my: 2 }} />
          </Box>
        )}
        {resourceTemplates &&
          Array.isArray(resourceTemplates) &&
          resourceTemplates.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography
                variant="subtitle1"
                gutterBottom
                component="div"
                sx={{ fontWeight: "bold" }}
              >
                Resource Templates
              </Typography>
              {resourceTemplates.map((template, index) => (
                <MCPServerResourceTemplate
                  key={index}
                  template={template}
                />
              ))}
              <Divider sx={{ my: 2 }} />
            </Box>
          )}
        {prompts && Array.isArray(prompts) && prompts.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography
              variant="subtitle1"
              gutterBottom
              component="div"
              sx={{ fontWeight: "bold" }}
            >
              Prompts
            </Typography>
            {prompts.map((prompt, index) => (
              <MCPServerPrompt key={index} prompt={prompt} />
            ))}
            <Divider sx={{ my: 2 }} />
          </Box>
        )}
        <Accordion
          sx={{ boxShadow: "none", "&:before": { display: "none" }, mt: 2 }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="raw-json-content"
            id="raw-json-header"
            sx={{
              minHeight: "40px", // Reduced height for summary
              "& .MuiAccordionSummary-content": {
                // Target content for margin
                margin: "8px 0",
              },
              borderTop: "1px solid rgba(0, 0, 0, 0.12)", // Add a top border
              borderBottom: "1px solid rgba(0, 0, 0, 0.12)", // Add a bottom border when closed
              "&.Mui-expanded": {
                // Remove bottom border when expanded
                borderBottom: "none",
              },
            }}
          >
            <Typography sx={{ fontWeight: "medium" }}>Raw Json</Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 0, pt: 1 }}>
            {" "}
            {/* Remove padding from details and add padding top */}
            <Typography
              component="pre"
              sx={{
                whiteSpace: "pre-wrap", // Handles long lines
                wordBreak: "break-all", // Breaks long words/strings
                fontSize: "0.875rem", // Standard small font size
                fontFamily: "monospace",
                backgroundColor: "rgba(0,0,0,0.03)", // Slight background for the code block
                padding: 1,
                borderRadius: 1,
                overflowX: "auto", // Add scroll for very wide content
                mt: 1, // Margin top for separation from summary
              }}
            >
              {prettyJson}
            </Typography>
          </AccordionDetails>
        </Accordion>
      </CardContent>
    </Card>
  );
};

export default MCPServerCard;
