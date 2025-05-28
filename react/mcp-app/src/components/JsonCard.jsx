import React from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';

const JsonCard = ({ jsonData, title }) => {
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

  const prettyJson = JSON.stringify(displayData, null, 2);

  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      {cardTitle && (
        <Box sx={{ p: 2, borderBottom: '1px solid rgba(0, 0, 0, 0.12)' }}>
          <Typography variant="h6" component="div">
            {cardTitle}
          </Typography>
        </Box>
      )}
      <CardContent>
        <Typography
          component="pre"
          sx={{
            whiteSpace: 'pre-wrap', // Handles long lines
            wordBreak: 'break-all', // Breaks long words/strings
            fontSize: '0.875rem', // Standard small font size
            fontFamily: 'monospace',
            backgroundColor: 'rgba(0,0,0,0.03)', // Slight background for the code block
            padding: 1,
            borderRadius: 1,
            overflowX: 'auto', // Add scroll for very wide content
          }}
        >
          {prettyJson}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default JsonCard;