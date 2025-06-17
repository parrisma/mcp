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

    const unescapeStringForInitialParse = (str) => {
      if (typeof str !== 'string') return str;
      try {
        let processed = str;
        processed = processed.replace(/\\\\/g, '\\');
        processed = processed.replace(/\\"/g, '"');
        processed = processed.replace(/\\n/g, '');
        processed = processed.replace(/\\t/g, '');
        return processed;
      } catch (err) { // eslint-disable-line no-unused-vars
        // console.warn("Error during initial string unescaping:", err);
        return str;
      }
    };

    const deepParseJsonStrings = (value) => {
      if (typeof value === 'string') {
        try {
          // Attempt to parse the string value directly.
          // Assumes initial global unescape has already prepared it if it was part of the top-level block.
          const parsed = JSON.parse(value);
          // If parsing succeeds, recursively process this newly parsed object/array.
          return deepParseJsonStrings(parsed);
        } catch (e) { // eslint-disable-line no-unused-vars
          // Not a JSON string, or malformed. Return string as is.
          return value;
        }
      } else if (Array.isArray(value)) {
        return value.map(item => deepParseJsonStrings(item));
      } else if (typeof value === 'object' && value !== null) {
        const newObj = {};
        for (const key in value) {
          if (Object.prototype.hasOwnProperty.call(value, key)) {
            newObj[key] = deepParseJsonStrings(value[key]);
          }
        }
        return newObj;
      }
      return value; // For numbers, booleans, null
    };

    let jsonMatch;
    jsonBlockRegex.lastIndex = 0;

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
      const rawJsonContent = jsonMatch[1]; // Content between ```json ... ```
      // Ensure rawJsonContent is a single line by removing newlines before further processing
      const singleLineRawJsonContent = typeof rawJsonContent === 'string' ? rawJsonContent.replace(/\r?\n|\r/g, '') : rawJsonContent;
      let formattedJsonBlock = jsonMatch[0]; // Default to the original full block text

      let preparedStringForTopLevelParse; // Declare here for access in catch
      try {
        const countOccurrences = (mainStr, subStr) => {
          if (!mainStr || !subStr || typeof mainStr !== 'string' || typeof subStr !== 'string') {
            return 0;
          }
          return mainStr.split(subStr).length - 1;
        };

        // Log count of \\" before unescaping
        console.log(
          "Count of '\"' before unescapeStringForInitialParse:",
          countOccurrences(singleLineRawJsonContent, '\\"')
        );

        // Step 1: Perform minimal unescaping for the top-level JSON structure
        preparedStringForTopLevelParse = unescapeStringForInitialParse(singleLineRawJsonContent); // Assign here
        
        // Log count of \\" after unescaping
        console.log(
          "Count of '\"' after unescapeStringForInitialParse:",
          countOccurrences(preparedStringForTopLevelParse, '\\"')
        );
        
        // Step 2: Parse this prepared string to get the top-level JS object/array
        console.log("Attempting JSON.parse on (preparedStringForTopLevelParse):", preparedStringForTopLevelParse);
        const topLevelJavaScriptObject = JSON.parse(preparedStringForTopLevelParse);
        console.log("After top-level JSON.parse (topLevelJavaScriptObject):", topLevelJavaScriptObject);
        
        // Step 3: Recursively parse any string values within this structure that are themselves JSON
        const deeplyParsedObject = deepParseJsonStrings(topLevelJavaScriptObject);
        console.log("After deepParseJsonStrings (deeplyParsedObject):", deeplyParsedObject);
        
        // Step 4: Stringify the final, deeply parsed object for pretty display
        formattedJsonBlock = "```json\n" + JSON.stringify(deeplyParsedObject, null, 2) + "\n```";

      } catch (error) { // eslint-disable-line no-unused-vars
        console.error(`Error during JSON processing for key ${baseKey}-json-${jsonLastIndex}:`, error);
        console.error("Original rawJsonContent that led to error:", rawJsonContent);
        console.error("singleLineRawJsonContent that led to error:", singleLineRawJsonContent);
        if (preparedStringForTopLevelParse !== undefined) {
          console.error("preparedStringForTopLevelParse that led to error:", preparedStringForTopLevelParse);
          // Fallback to displaying the prepared string (after initial unescape) if parsing failed
          formattedJsonBlock = "```json\n" + preparedStringForTopLevelParse + "\n```";
        } else {
          // If preparedStringForTopLevelParse is somehow undefined (e.g., error in unescapeStringForInitialParse itself),
          // then fall back to the original match. This is a deeper fallback.
          formattedJsonBlock = jsonMatch[0];
        }
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