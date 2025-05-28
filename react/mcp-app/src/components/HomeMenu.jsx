import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';

function HomeMenu({ onViewChange }) {
  return (
    <Box sx={{ display: "flex", gap: 1 }}>
      <Button color="primary" onClick={() => onViewChange('Question')}>Question</Button>
      <Button color="primary" onClick={() => onViewChange('Settings')}>Settings</Button>
    </Box>
  );
}

export default HomeMenu;