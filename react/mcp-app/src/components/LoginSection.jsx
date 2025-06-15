import React from 'react';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Button from '@mui/material/Button';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';

const loginSectionPaperStyle = {
  padding: 3,
  border: '1px solid rgba(255, 255, 255, 0.23)',
  width: '100%',
  minHeight: '160px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  backgroundColor: 'transparent',
};

const formControlStyle = {
  minWidth: 180,
  marginRight: 1,
};

const textFieldStyle = {
    marginRight: 1,
};

const roles = [
  "Sales Trader",
  "Execution Trader",
  "Operations",
  "Finance",
  "Technology",
  "Compliance"
];

// Props: role, setRole, username, setUsername, handleLogin (from App.jsx), loginMessage (from App.jsx)
function LoginSection({
  role,
  setRole,
  username,
  setUsername,
  handleLogin, // This function will be called to perform actual login logic in App.jsx
  loginMessage // This prop will carry the message from App.jsx
}) {
  // Local message state is removed, will use loginMessage prop from App.jsx
  // const [message, setMessage] = useState('Please enter your credentials and click Login.');

  // useEffect to update local display if loginMessage prop changes
  // This is not strictly necessary if we directly display loginMessage,
  // but useful if we wanted to combine it with other local messages.
  // For now, we'll directly display loginMessage.

  const onLoginButtonClick = () => {
    // Call the handleLogin function passed from App.jsx
    // App.jsx will be responsible for setting the global loginMessage
    if (handleLogin) {
      handleLogin(username, role);
    }
  };

  return (
    <Paper sx={loginSectionPaperStyle} elevation={0} variant="outlined">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 2,
          width: '100%',
          paddingX: 2,
        }}
      >
        <Box
          component="form"
          sx={{
            display: 'flex',
            flexDirection: 'row',
            alignItems: 'center',
            gap: 2,
            width: 'fit-content',
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
            onClick={onLoginButtonClick} // Call the new handler
            size="medium"
          >
            Login
          </Button>
        </Box>
        <TextField
          label="Message"
          variant="outlined"
          value={loginMessage} // Display the message from App.jsx props
          size="small"
          fullWidth
          InputProps={{
            readOnly: true,
          }}
        />
      </Box>
    </Paper>
  );
}

export default LoginSection;