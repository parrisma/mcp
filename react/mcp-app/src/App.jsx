import { useState } from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Grid from "@mui/material/Grid";
import { v4 as uuidv4 } from 'uuid'; // Import UUID generator
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
  const [sessionId, setSessionId] = useState(uuidv4().toUpperCase()); // Manage sessionId in App.jsx

  const [activeView, setActiveView] = useState("Question");
  const darkTheme = createTheme({
    palette: {
      mode: "dark",
    },
    typography: {
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    },
    components: {
      MuiTextField: {
        styleOverrides: {
          root: {
            "& .MuiInputBase-root": {
              fontSize: "0.875rem", // Apply to input text
            },
            "& .MuiInputLabel-root": {
              fontSize: "0.875rem", // Apply to label
            },
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          // Style for the disabled state
          root: {
            fontSize: "0.875rem", // Apply font size to buttons
            '&.Mui-disabled': {
              backgroundColor: '#ccc', // Gray background
              color: '#666', // Darker gray text color
            },
          },
        },
      },
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
    setSessionId(uuidv4().toUpperCase()); // Generate a new session ID on reset
  };

  // This is the callback for the main Prompt component
  const handlePromptSubmitResponse = async (statusUpdate, submittedGoal) => {
    if (submittedGoal && statusUpdate.loading && !apiStatus.loading) {
      // This is a new submission from Prompt.jsx
      setCurrentGoalPromptText(submittedGoal);
      // Generate and set a *new* session ID for this new question
      const newSessionId = uuidv4().toUpperCase();
      setSessionId(newSessionId);
      setApiStatus({ ...statusUpdate, data: null, error: null, startTime: Date.now() });

      // Now construct and make the API call in App.jsx using the *newly generated* session ID
      try {
        const fullUrl = `${baseApiUrl}/model_response?goal=${encodeURIComponent(
          submittedGoal
        )}&session=${newSessionId}`; // Use the newly generated session ID

        const response = await fetch(fullUrl);

        if (!response.ok) {
          const errorData = await response
            .json()
            .catch(() => ({ error: `HTTP error: ${response.status}` }));
          throw new Error(errorData.error || `HTTP error: ${response.status}`);
        }

        const responseText = await response.text();
        console.log("Raw server response:", responseText); // Log the raw response
        const responseData = JSON.parse(responseText); // Parse the text as JSON
        // Pass the received data back to App.jsx
        setApiStatus({ data: responseData, loading: false, error: null });

      } catch (err) {
        // Pass the error back to App.jsx
        setApiStatus({ data: null, loading: false, error: err.message });
      }
    } else if (statusUpdate.loading && !apiStatus.loading) {
      // This might be from "Do Next Steps" or a re-submission without changing goal
      // Ensure data isn't prematurely cleared if it's a next step
      setApiStatus(prevStatus => ({ ...prevStatus, ...statusUpdate, startTime: Date.now() }));
    } else if (!statusUpdate.loading && apiStatus.loading) {
      setApiStatus({ ...statusUpdate, startTime: null });
    } else {
      setApiStatus(prevStatus => ({...prevStatus, ...statusUpdate}));
    }
  };
  
  // This callback can be simplified for Status component's "Do Next Steps"
  // as it won't set the currentGoalPromptText and should not change the sessionId
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
          <Grid>
            <Paper sx={homePaper}>
              <HomeMenu onViewChange={handleViewChange} />
            </Paper>
          </Grid>
          <Grid xs={12}>
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
                  sessionId={sessionId} // Pass sessionId to Prompt
                  setSessionId={setSessionId} // Pass setSessionId to Prompt
                  isLoading={apiStatus.loading} // Pass loading state to Prompt
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
            <Grid>
              <Paper sx={homePaper}>
                <Status
                  apiStatus={apiStatus}
                  baseApiUrl={baseApiUrl}
                  onApiResponse={handleNextStepsApiResponse} // Use the specific handler for "Do Next Steps"
                  lastResponseData={apiStatus.data}
                  currentGoalPromptText={currentGoalPromptText} // Pass the original goal
                  sessionId={sessionId} // Pass sessionId to Status
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
