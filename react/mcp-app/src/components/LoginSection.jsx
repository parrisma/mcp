import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Button from '@mui/material/Button';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';

const loginSectionPaperStyle = {
  padding: 3, // Increased padding for better spacing
  border: '1px solid rgba(255, 255, 255, 0.23)',
  width: '100%',
  minHeight: '160px', // Approximate height for 10 lines
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center', // Center the horizontal Box
  backgroundColor: 'transparent',
};

const formControlStyle = {
  minWidth: 180, // Ensure dropdown has a decent width
  marginRight: 1, // Add some margin to the right of the dropdown
};

const textFieldStyle = {
    marginRight: 1, // Add some margin to the right of the text field
}

const roles = [
  "Sales Trader",
  "Execution Trader",
  "Operations",
  "Finance",
  "Technology",
  "Compliance"
];

function LoginSection() {
  const [username, setUsername] = useState('');
  const [role, setRole] = useState('');
  const [message, setMessage] = useState('Please enter your credentials and click Login.'); // Initial message

  const handleLogin = () => {
    // Placeholder for login logic
    console.log("Login attempt with:", { username, role });
    if (username && role) {
      setMessage(`${username} you are now connected as ${role} role`);
    } else if (!username && role) {
      setMessage("User Name is required.");
    } else if (username && !role) {
      setMessage("Role is required.");
    }
    else {
      setMessage("User Name and Role are required.");
    }
  };

  return (
    <Paper sx={loginSectionPaperStyle} elevation={0} variant="outlined">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column', // Parent box for vertical arrangement
          alignItems: 'center', // Center items horizontally
          gap: 2, // Spacing between the form row and the message field
          width: '100%', // Take full width to allow message field to span
          paddingX: 2, // Add some horizontal padding if message field is too wide
        }}
      >
        <Box
          component="form"
          sx={{
            display: 'flex',
            flexDirection: 'row', // Arrange form items horizontally
            alignItems: 'center',
            gap: 2,
            width: 'fit-content', // Keep form itself centered
          }}
          noValidate
          autoComplete="off"
        >
          <TextField
            label="User Name"
            variant="outlined"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            size="small"
            sx={textFieldStyle}
          />
          <FormControl variant="outlined" size="small" sx={formControlStyle}>
            <InputLabel id="role-select-label">Role</InputLabel>
            <Select
              labelId="role-select-label"
              id="role-select"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              label="Role"
            >
              <MenuItem value="">
                <em>None</em>
              </MenuItem>
              {roles.map((roleName) => (
                <MenuItem key={roleName} value={roleName}>
                  {roleName}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Button
            variant="contained"
            onClick={handleLogin}
            size="medium"
          >
            Login
          </Button>
        </Box>
        <TextField
          label="Message"
          variant="outlined"
          value={message} // Bind to message state
          size="small"
          fullWidth // Make it take the full width of its parent
          InputProps={{
            readOnly: true,
          }}
          // Optional: if you want a fixed number of rows for the message
          // multiline
          // rows={2}
        />
      </Box>
    </Paper>
  );
}

export default LoginSection;