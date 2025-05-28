import { useState } from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Grid from "@mui/material/Grid";
import Status from "./components/Status.jsx";
import HomeMenu from "./components/HomeMenu.jsx";
import Prompt from "./components/Prompt.jsx";
import SettingsAndStatus from "./components/SettingsAndStatus.jsx";

const homePaper = {
  padding: 2,
  textAlign: "left",
  height: "100%",
  elevation: 3,
};

const homeLayout = {
  minHeight: "100vh",
  width: "100vw",
  display: "flex",
  alignItems: "stretch",
  justifyContent: "center",
};

const homeLayoutGrid = {
  flex: 1,
  height: "100%",
};

const mainGridProps = {
  container: true,
  direction: "column",
  spacing: 1,
  alignItems: "stretch",
};

function App() {
  const [statusMessage, _setStatusMessage] = useState("Ready.");
  const [activeView, setActiveView] = useState("Question");
  const darkTheme = createTheme({
    palette: {
      mode: "dark",
    },
    typography: {
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    },
  });

  const handleViewChange = (view) => {
    setActiveView(view);
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={homeLayout}>
        <Grid {...mainGridProps} sx={homeLayoutGrid}>
          <Grid item>
            <Paper sx={homePaper}>
              <HomeMenu onViewChange={handleViewChange} />
            </Paper>
          </Grid>
          <Grid item xs>
            <Paper
              sx={{
                ...homePaper,
                display: "flex",
                flexDirection: "column",
                flexGrow: 1,
              }}
            >
              {activeView === "Question" && <Prompt />}
              {activeView === "Settings" && <SettingsAndStatus />}
            </Paper>
          </Grid>
          {activeView !== "Settings" && (
            <Grid item>
              <Paper sx={homePaper}>
                <Status message={statusMessage} />
              </Paper>
            </Grid>
          )}
        </Grid>
      </Box>
    </ThemeProvider>
  );
}

export default App;
