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
  // Lifted state for API URL construction
  const [clientHostValue, setClientHostValue] = useState("localhost");
  const [clientPortValue, setClientPortValue] = useState("9312");

  // State for API response from Prompt
  const [apiStatus, setApiStatus] = useState({
    data: null,
    loading: false,
    error: null,
    startTime: null,
  });
  const [currentGoalPromptText, setCurrentGoalPromptText] = useState(""); // Store the original goal

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

  const baseApiUrl = `http://${clientHostValue}:${clientPortValue}`;

  // Determine if "Next Steps" are available and not "None"
  const nextStepsFromApi = apiStatus.data?.response?.thinking?.next_steps;
  const isNextStepsAvailable =
    nextStepsFromApi &&
    nextStepsFromApi.trim() !== "" &&
    nextStepsFromApi.toLowerCase().trim() !== "none";

  const handleResetAll = () => {
    setApiStatus({
      data: null,
      loading: false,
      error: null,
      startTime: null,
    });
    setCurrentGoalPromptText(""); // Clear the stored goal on reset
  };

  // This is the callback for the main Prompt component
  const handlePromptSubmitResponse = (statusUpdate, submittedGoal) => {
    if (submittedGoal && statusUpdate.loading && !apiStatus.loading) {
      // This is a new submission from Prompt.jsx
      setCurrentGoalPromptText(submittedGoal);
      setApiStatus({ ...statusUpdate, data: null, error: null, startTime: Date.now() });
    } else if (statusUpdate.loading && !apiStatus.loading) {
      // This might be from "Do Next Steps" or a re-submission without changing goal
      // Ensure data isn't prematurely cleared if it's a next step
      setApiStatus(prevStatus => ({ ...prevStatus, ...statusUpdate, startTime: Date.now() }));
    } else if (!statusUpdate.loading && apiStatus.loading) {
      setApiStatus({ ...statusUpdate, startTime: null });
    } else {
      setApiStatus(prevStatus => ({ ...prevStatus, ...statusUpdate }));
    }
  };
  
  // This callback can be simplified for Status component's "Do Next Steps"
  // as it won't set the currentGoalPromptText
  const handleNextStepsApiResponse = (statusUpdate) => {
     if (statusUpdate.loading && !apiStatus.loading) {
        setApiStatus(prevStatus => ({ ...prevStatus, ...statusUpdate, data: prevStatus.data, startTime: Date.now() }));
     } else if (!statusUpdate.loading && apiStatus.loading) {
        setApiStatus({ ...statusUpdate, startTime: null });
     } else {
        setApiStatus(prevStatus => ({...prevStatus, ...statusUpdate}));
     }
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
              {activeView === "Question" && (
                <Prompt
                  baseApiUrl={baseApiUrl}
                  onApiResponse={handlePromptSubmitResponse} // Use the new handler
                  isNextStepsMode={isNextStepsAvailable}
                  onResetAll={handleResetAll}
                />
              )}
              {activeView === "Settings" && (
                <SettingsAndStatus
                  clientHostValue={clientHostValue}
                  setClientHostValue={setClientHostValue}
                  clientPortValue={clientPortValue}
                  setClientPortValue={setClientPortValue}
                />
              )}
            </Paper>
          </Grid>
          {/* Status component is always visible now, or conditionally based on activeView if preferred */}
          {/* For now, let's make it always visible below the main content area if not in settings */}
          {activeView !== "Settings" && (
            <Grid item>
              <Paper sx={homePaper}>
                <Status
                  apiStatus={apiStatus}
                  baseApiUrl={baseApiUrl}
                  onApiResponse={handleNextStepsApiResponse} // Use the specific handler for "Do Next Steps"
                  lastResponseData={apiStatus.data}
                  currentGoalPromptText={currentGoalPromptText} // Pass the original goal
                />
              </Paper>
            </Grid>
          )}
        </Grid>
      </Box>
    </ThemeProvider>
  );
}

export default App;
