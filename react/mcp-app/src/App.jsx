import { useState, useEffect } from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Grid from "@mui/material/Grid";
import { v4 as uuidv4 } from "uuid"; // Import UUID generator
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
  const [clarificationResponses, setClarificationResponses] = useState([]); // State to hold clarification responses
  const [elapsedSeconds, setElapsedSeconds] = useState(0); // State for elapsed time
  const [isProcessingNextSteps, setIsProcessingNextSteps] = useState(false); // New state for "Do Next Steps" processing

  useEffect(() => {
    let intervalId;
    // Use apiStatus.loading OR isProcessingNextSteps to determine if timer should run
    if ((apiStatus.loading || isProcessingNextSteps) && apiStatus.startTime) {
      setElapsedSeconds(Math.floor((Date.now() - apiStatus.startTime) / 1000)); // Initial calculation
      intervalId = setInterval(() => {
        setElapsedSeconds(
          Math.floor((Date.now() - apiStatus.startTime) / 1000)
        );
      }, 1000);
    } else {
      setElapsedSeconds(0); // Reset when not loading/processing or no startTime
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [apiStatus.loading, isProcessingNextSteps, apiStatus.startTime]); // Add isProcessingNextSteps to dependency array

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
            "&.Mui-disabled": {
              backgroundColor: "#ccc", // Gray background
              color: "#666", // Darker gray text color
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
    // Explicitly check if submittedGoal is provided and not empty for a new submission
    if (
      submittedGoal &&
      submittedGoal.trim() !== "" &&
      statusUpdate.loading &&
      !apiStatus.loading
    ) {
      // This is a new submission from Prompt.jsx
      setCurrentGoalPromptText(submittedGoal);
      const newSessionId = uuidv4().toUpperCase();
      setSessionId(newSessionId);
      setApiStatus({
        ...statusUpdate,
        data: null,
        error: null,
        startTime: Date.now(),
      });

      // Now construct and make the API call in App.jsx using the *newly generated* session ID
      try {
        const fullUrl = `${baseApiUrl}/model_response`;
        const requestBody = {
          goal: submittedGoal,
          session: newSessionId
        };
        console.log("SUBMIT - Making POST request to:", fullUrl, "with body:", requestBody); // Updated console log

        const response = await fetch(fullUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
          const errorData = await response
            .json()
            .catch(() => ({ error: `HTTP error: ${response.status}` }));
          throw new Error(errorData.error || `HTTP error: ${response.status}`);
        }

        const responseText = await response.text();
        console.log("SUBMIT - Raw server response:", responseText); // Log the raw response
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
      setApiStatus((prevStatus) => ({
        ...prevStatus,
        ...statusUpdate,
        startTime: Date.now(),
      }));
    } else if (!statusUpdate.loading && apiStatus.loading) {
      setApiStatus({ ...statusUpdate, startTime: null });
    } else {
      setApiStatus((prevStatus) => ({ ...prevStatus, ...statusUpdate }));
    }
  };

  // Handler for clarification responses from Status component
  const handleClarificationResponses = (responses) => {
    setClarificationResponses(responses);
  };

  // This callback can be simplified for Status component's "Do Next Steps"
  // as it won't set the currentGoalPromptText and should not change the sessionId
  // This callback can be simplified for Status component's "Do Next Steps"
  // as it won't set the currentGoalPromptText and should not change the sessionId
  const handleNextStepsApiResponse = async (statusUpdate) => {
    // Add a unique identifier for each invocation of this function
    const invocationId = Date.now() + '-' + Math.floor(Math.random() * 1000);
    
    console.log(
      `[ID:${invocationId}] handleNextStepsApiResponse called with statusUpdate:`,
      statusUpdate
    );

    if (statusUpdate.loading && !apiStatus.loading) {
      console.log(`[ID:${invocationId}] Starting processing - setting isProcessingNextSteps=true`);
      setIsProcessingNextSteps(true); // Start processing indicator
      setApiStatus((prevStatus) => ({
        ...prevStatus,
        ...statusUpdate,
        data: prevStatus.data,
        startTime: Date.now(),
      }));

      try {
        const fullUrl = `${baseApiUrl}/model_response`;
        const params = new URLSearchParams();
        params.append("goal", currentGoalPromptText);
        params.append("session", sessionId);

        const requestBody = {
          ...apiStatus.data,
          goal: currentGoalPromptText, // Explicitly include goal in body
          session: sessionId, // Explicitly include session in body
          clarifications: clarificationResponses, // Include captured clarification responses
        };

        const fullUrlWithParams = `${fullUrl}?${params.toString()}`; // Construct URL with params for logging
        console.log(`[ID:${invocationId}] NEXT STEPS - Making POST request to:`, fullUrlWithParams);
        console.log(`[ID:${invocationId}] NEXT STEPS - Request body:`, requestBody);
        console.log(`[ID:${invocationId}] NEXT STEPS - clarificationResponses:`, clarificationResponses);

        const response = await fetch(fullUrl, {
          method: "POST", // Use POST for sending body
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
        });
        console.log(`[ID:${invocationId}] NEXT STEPS - POST returned response:`, response);

        if (!response.ok) {
          const errorData = await response
            .json()
            .catch(() => ({ error: `HTTP error: ${response.status}` }));
          console.log(`[ID:${invocationId}] NEXT STEPS - Error response:`, errorData);
          throw new Error(errorData.error || `HTTP error: ${response.status}`);
        }
        const responseData = await response.json();
        console.log(`[ID:${invocationId}] NEXT STEPS - Raw server response:`, responseData);
        console.log(`[ID:${invocationId}] NEXT STEPS - Setting apiStatus with data and loading=false`);
        setApiStatus({ data: responseData, loading: false, error: null });
        setIsProcessingNextSteps(false); // End processing indicator on success
      } catch (err) {
        console.log(`[ID:${invocationId}] NEXT STEPS - Caught error:`, err.message);
        setApiStatus({
          data: apiStatus.data,
          loading: false,
          error: err.message,
        });
        setIsProcessingNextSteps(false); // End processing indicator on error
      }
    } else if (!statusUpdate.loading && apiStatus.loading) {
      setApiStatus({ ...statusUpdate, startTime: null });
    } else {
      setApiStatus((prevStatus) => ({ ...prevStatus, ...statusUpdate }));
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
                  isLoading={apiStatus.loading || isProcessingNextSteps} // Pass combined loading state to Prompt
                  activityStatus={
                    apiStatus.loading || isProcessingNextSteps
                      ? `thinking, please be patient [${elapsedSeconds}s]`
                      : ""
                  } // Pass activity status based on combined state
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
                  onClarificationResponsesChange={handleClarificationResponses} // Pass the handler to Status
                  onResetAll={handleResetAll} // Pass the reset handler to Status
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
