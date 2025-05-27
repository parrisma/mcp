import { useState } from 'react';
import CssBaseline from '@mui/material/CssBaseline';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import reactLogo from './assets/react.svg';
import viteLogo from '/vite.svg';
// It's good practice to remove unused CSS if MUI is handling most of the styling
// import './App.css';

function App() {
  const [count, setCount] = useState(0);

  return (
    <>
      <CssBaseline />
      <Container maxWidth="sm">
        <Box
          sx={{
            my: 4,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          <Box sx={{ mb: 2, display: 'flex', gap: '16px' }}>
            <Link href="https://vite.dev" target="_blank" rel="noopener">
              <img src={viteLogo} className="logo" alt="Vite logo" style={{ height: '6em', padding: '1.5em' }} />
            </Link>
            <Link href="https://react.dev" target="_blank" rel="noopener">
              <img src={reactLogo} className="logo react" alt="React logo" style={{ height: '6em', padding: '1.5em' }} />
            </Link>
          </Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Vite + React + MUI
          </Typography>
          <Typography variant="body1" gutterBottom>
            Welcome to your MUI-enhanced application!
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Button variant="contained" onClick={() => setCount((count) => count + 1)}>
              Count is {count}
            </Button>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Edit <code>src/App.jsx</code> and save to test HMR.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Click on the Vite and React logos to learn more.
          </Typography>
        </Box>
      </Container>
    </>
  );
}

export default App;
