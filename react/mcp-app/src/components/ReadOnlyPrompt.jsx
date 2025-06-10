import React from 'react';
import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';
import PropTypes from 'prop-types';

function ReadOnlyPrompt({ label, value }) {
  return (
    <Box sx={{ width: '100%', overflow: 'auto' }}>
      <TextField
        label={label}
        value={value}
        variant="outlined"
        fullWidth
        multiline
        rows={30} // Set fixed height to 30 rows
        InputProps={{
          readOnly: true,
          sx: {
            overflow: 'auto', // Enable scrolling
            whiteSpace: 'pre-wrap', // Preserve whitespace and wrap text
            wordBreak: 'break-word', // Break long words
          },
        }}
        sx={{
          '& .MuiInputBase-root': {
            overflow: 'auto', // Enable scrolling for the input area
          },
        }}
      />
    </Box>
  );
}

ReadOnlyPrompt.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
};

export default ReadOnlyPrompt;