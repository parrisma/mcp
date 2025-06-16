import React from 'react';
import PropTypes from 'prop-types';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

// Unused constants related to old regex removed.

function ColoredPromptDisplay({ label, promptText, colors: colorsProp }) { // Renamed colors to colorsProp
  const jsonBlockRegex = /```json\r?\n([\s\S]*?)\r?\n```/g;

  // Ensure colors is always an array, falling back to a default if not provided or empty
  const colors = (colorsProp && colorsProp.length > 0)
    ? colorsProp
    : ['#66CCCC', '#FFB347', '#B284BE', '#77DD77', '#FF6961', '#FDFD96', '#836953', '#FFD1DC']; // Default palette

  if (!promptText) {
    // Render an empty state that still respects the label and minHeight
    return (
      <Box
        sx={{
          width: '100%',
          border: '1px solid rgba(255, 255, 255, 0.23)',
          borderRadius: '4px',
          position: 'relative',
          fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
          fontSize: '0.875rem',
          height: `calc(30 * 1.43em + ${16.5 * 2}px + 2px)`, // Approx 30 rows + padding + border
          padding: '16.5px 14px', // Standard MUI TextField padding
          boxSizing: 'border-box',
        }}
      >
        <Typography
          component="label"
          sx={{
            color: 'rgba(255, 255, 255, 0.7)',
            padding: '0 5px',
            fontSize: '0.75rem',
            fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
            lineHeight: '1.4375em',
            display: 'block',
            position: 'absolute',
            top: '-0.7em',
            left: '10px',
            backgroundColor: (theme) => theme.palette.background.default, // Use theme background
            zIndex: 1,
          }}
        >
          {label}
        </Typography>
        <Typography component="span" sx={{ whiteSpace: 'pre-wrap', display: 'block', paddingTop: '0.5em' }}>&nbsp;</Typography>
      </Box>
    );
  }

  const formatJsonInText = (text, color, baseKey) => {
    const jsonDisplayParts = [];
    let jsonLastIndex = 0;
    let jsonMatch;
    jsonBlockRegex.lastIndex = 0; // Reset regex for current text

    while ((jsonMatch = jsonBlockRegex.exec(text)) !== null) {
      // Text before JSON block
      if (jsonMatch.index > jsonLastIndex) {
        jsonDisplayParts.push(
          <Typography component="span" key={`${baseKey}-text-${jsonLastIndex}`} sx={{ color, whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: '0.875rem' }}>
            {text.substring(jsonLastIndex, jsonMatch.index)}
          </Typography>
        );
      }

      // The JSON block itself
      const jsonContent = jsonMatch[1];
      let formattedJsonBlock = jsonMatch[0]; // Default to original block text
      try {
        const parsed = JSON.parse(jsonContent);
        formattedJsonBlock = "```json\n" + JSON.stringify(parsed, null, 2) + "\n```";
      } catch (error) { // eslint-disable-line no-unused-vars
        // Parsing failed, leave as original
        // Optionally log the actual error for debugging: console.warn("Failed to parse JSON block for key:", `${baseKey}-json-${jsonLastIndex}`, error);
        console.warn("Failed to parse JSON block, leaving as is for key:", `${baseKey}-json-${jsonLastIndex}`);
      }
      jsonDisplayParts.push(
        <Typography component="span" key={`${baseKey}-json-${jsonLastIndex}`} sx={{ color, whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: '0.875rem' }}>
          {formattedJsonBlock}
        </Typography>
      );
      jsonLastIndex = jsonBlockRegex.lastIndex;
    }

    // Remaining text after last JSON block
    if (jsonLastIndex < text.length) {
      jsonDisplayParts.push(
        <Typography component="span" key={`${baseKey}-text-${jsonLastIndex}-final`} sx={{ color, whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: '0.875rem' }}>
          {text.substring(jsonLastIndex)}
        </Typography>
      );
    }
    return jsonDisplayParts;
  };

  const parts = [];
  let keyIndex = 0;
  let colorIdx = 0;
  // Regex to match dynamic section names: <<SECTION_NAME SECTION - START>>...content...<<SECTION_NAME SECTION - END>>
  // Group 1: Full start tag (e.g., "<<GOAL SECTION - START>>")
  // Group 2: Section name (e.g., "GOAL")
  // Group 3: Section content
  // Group 4: Full end tag (e.g., "<<GOAL SECTION - END>>")
  const sectionRegex = /(<<([A-Z\s_]+) SECTION - START>>)(.*?)(<<\2 SECTION - END>>)/gs;
  let lastIndex = 0;
  let match;

  while ((match = sectionRegex.exec(promptText)) !== null) {
    // Text before this match
    if (match.index > lastIndex) {
      parts.push(
        <Typography component="span" key={`text-${keyIndex++}`} sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: '0.875rem' }}>
          {promptText.substring(lastIndex, match.index)}
        </Typography>
      );
    }

    // Start marker (match[1])
    parts.push(
      <Typography component="span" key={`start-${keyIndex++}`} sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: '0.875rem' }}>
        {match[1]}
      </Typography>
    );

    // Section content (colored) (match[3])
    if (match[3]) {
      const sectionColor = colors[colorIdx % colors.length];
      const formattedContentParts = formatJsonInText(match[3], sectionColor, `content-section-${keyIndex}`);
      // Wrap in a fragment that gets the main part key
      parts.push(
        <React.Fragment key={`content-wrapper-${keyIndex++}`}>
          {formattedContentParts}
        </React.Fragment>
      );
      colorIdx++;
    }

    // End marker (match[4])
    parts.push(
      <Typography component="span" key={`end-${keyIndex++}`} sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: '0.875rem' }}>
        {match[4]}
      </Typography>
    );

    lastIndex = sectionRegex.lastIndex;
  }

  // Any remaining text after the last match
  if (lastIndex < promptText.length) {
    parts.push(
      <Typography component="span" key={`text-${keyIndex++}`} sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: '0.875rem' }}>
        {promptText.substring(lastIndex)}
      </Typography>
    );
  }

  return (
    <Box
      sx={{
        width: '100%',
        border: '1px solid rgba(255, 255, 255, 0.23)',
        borderRadius: '4px',
        position: 'relative',
        fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
        fontSize: '0.875rem',
        height: `calc(30 * 1.43em + ${16.5 * 2}px + 2px)`, // Approx 30 rows + padding + border
        overflowY: 'auto',
        boxSizing: 'border-box',
      }}
    >
      <Typography
        component="label"
        sx={{
          color: 'rgba(255, 255, 255, 0.7)',
          padding: '0 5px',
          fontSize: '0.75rem',
          fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
          lineHeight: '1.4375em',
          display: 'block',
          position: 'absolute',
          top: '-0.7em',
          left: '10px',
          backgroundColor: (theme) => theme.palette.background.default, // Use theme background
          zIndex: 1,
        }}
      >
        {label}
      </Typography>
      <Box
        sx={{
          padding: '16.5px 14px',
          paddingTop: 'calc(16.5px + 0.5em)', // Adjust for label
          height: '100%',
        }}
      >
        {parts.map((part, index) => (
          <React.Fragment key={index}>{part}</React.Fragment>
        ))}
      </Box>
    </Box>
  );
}

ColoredPromptDisplay.propTypes = {
  label: PropTypes.string.isRequired,
  promptText: PropTypes.string, // Allow null or undefined for empty state
  colors: PropTypes.arrayOf(PropTypes.string),
};

ColoredPromptDisplay.defaultProps = {
  promptText: '',
  colors: ['#66CCCC', '#FFB347', '#B284BE', '#77DD77', '#FF6961', '#FDFD96', '#836953', '#FFD1DC'],
  // Teal, Orange, Purple, Pastel Green, Pastel Red, Pastel Yellow, Brown, Pink
};

export default ColoredPromptDisplay;