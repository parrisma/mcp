import { useState, useEffect } from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Grid from "@mui/material/Grid";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button"; // Import Button
import { v4 as uuidv4 } from "uuid"; // Import UUID generator
import Status from "./components/Status.jsx";
import HomeMenu from "./components/HomeMenu.jsx";
import Prompt from "./components/Prompt.jsx";
import SettingsAndStatus from "./components/SettingsAndStatus.jsx";
import MenuItem from "@mui/material/MenuItem"; // Import MenuItem
import ReadOnlyPrompt from "./components/ReadOnlyPrompt.jsx"; // Import ReadOnlyPrompt
import LoginSection from "./components/LoginSection.jsx"; // Import LoginSection

const homePaper = {
  padding: 2,
  textAlign: "left",
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
  const [promptText, setPromptText] = useState(""); // State for the main prompt text
  const [sessionId, setSessionId] = useState(uuidv4().toUpperCase()); // Manage sessionId in App.jsx
  const [clarificationResponses, setClarificationResponses] = useState([]); // State to hold clarification responses
  const [elapsedSeconds, setElapsedSeconds] = useState(0); // State for elapsed time
  const [isProcessingNextSteps, setIsProcessingNextSteps] = useState(false); // New state for "Do Next Steps" processing
  const [isFinalAnswerAvailable, setIsFinalAnswerAvailable] = useState(false); // State for whether a final answer is available
  const [username, setUsername] = useState(''); // For LoginSection
  const [staffId, setStaffId] = useState(''); // For LoginSection Staff ID
  const [role, setRole] = useState(''); // For LoginSection
  const [loginMessage, setLoginMessage] = useState('Please enter your credentials and click Login.'); // For LoginSection
  const [isGettingPrompts, setIsGettingPrompts] = useState(false); // State for Get Prompts button
 
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

  // Clear relevant states when sessionId changes
  useEffect(() => {
    setPromptText("");
    setApiStatus({
      data: null,
      loading: false,
      error: null,
      startTime: null,
    });
    setClarificationResponses([]);
    setIsProcessingNextSteps(false);
    setIsFinalAnswerAvailable(false);
    // Clear prompt-related states
    setPromptVersions([]);
    setSelectedPromptVersion("");
    setPromptsResponse("");
    setPromptsData([]);
  }, [sessionId]); // Dependency array includes sessionId

  const [activeView, setActiveView] = useState("Login"); // Default to Login view
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

  const [promptVersions, setPromptVersions] = useState([]); // New state for prompt versions
  const [selectedPromptVersion, setSelectedPromptVersion] = useState(""); // New state for selected version
  const [promptsResponse, setPromptsResponse] = useState(""); // New state for the response message
  const [promptsData, setPromptsData] = useState([]); // New state to store the full prompts data

  const handleGetPrompts = async () => {
    setIsGettingPrompts(true); // Set loading state
    const fullUrl = `${baseApiUrl}/prompts?session_id=${sessionId}`;
    console.log("Making GET request to:", fullUrl);
    try {
      const response = await fetch(fullUrl);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log("Prompts received:", data);
      if (data?.response?.prompts && data.response.prompts.length > 0) {
        setPromptsData(data.response.prompts); // Store the full prompts data
        const versions = data.response.prompts.map((p) => p.version);
        setPromptVersions(versions);
        console.log("Prompt versions set:", versions); // Added logging
        setSelectedPromptVersion(versions[0]); // Select the first version by default
        setPromptsResponse(""); // Clear previous response message on success
      } else {
        console.log("No matching prompts found for this session ID."); // Updated logging
        setPromptsData([]); // Clear prompts data
        setPromptVersions([]);
        setSelectedPromptVersion("");
        setPromptsResponse("No matching prompts"); // Set message for empty list
      }
    } catch (error) {
      console.error("Error fetching prompts:", error);
      setPromptsData([]); // Clear prompts data
      setPromptVersions([]);
      setSelectedPromptVersion("");
      setPromptsResponse(`Error fetching prompts: ${error.message}`); // Set error message
    } finally {
      setIsGettingPrompts(false); // Reset loading state
    }
  };

  // Find the prompt text for the selected version
  const selectedPromptText =
    promptsData.find((p) => p.version === selectedPromptVersion)?.prompt || "";

  const handleVersionChange = (event) => {
    setSelectedPromptVersion(event.target.value);
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
    setPromptText(""); // Clear the prompt text on reset
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
      // Do NOT generate a new session ID here. The session ID is managed on initial load and reset.
      setApiStatus({
        ...statusUpdate,
        data: null,
        error: null,
        startTime: Date.now(),
      });

      // Now construct and make the API call in App.jsx using the *current* session ID
      try {
        const fullUrl = `${baseApiUrl}/model_response`;
        const requestBody = {
          response: {
            // ...apiStatus.data?.response, - MP prev not needed ? Include previous response data if available
            clarifications: clarificationResponses, // Include current clarification responses
            mcp_server_calls: apiStatus.data?.response?.mcp_server_calls, // Include previous MCP calls if available
          },
          status: apiStatus.data?.status, // Include previous status
          goal: submittedGoal, // Use the submitted goal
          session: sessionId, // Use the current session ID
          user_role: role, // Add user_role
          staff_id: staffId, // Add staff_id
        };
        console.log(
          "SUBMIT - Making POST request to:",
          fullUrl,
          "with body:",
          requestBody
        ); // Updated console log

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
        // Set state based on whether a non-null/undefined answer is available
        setIsFinalAnswerAvailable(responseData?.response?.answer != null);
      } catch (err) {
        // Pass the error back to App.jsx
        setApiStatus({ data: null, loading: false, error: err.message });
        setIsFinalAnswerAvailable(false); // Reset state on error
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
    const invocationId = Date.now() + "-" + Math.floor(Math.random() * 1000);

    console.log(
      `[ID:${invocationId}] handleNextStepsApiResponse called with statusUpdate:`,
      statusUpdate
    );

    if (statusUpdate.loading && !apiStatus.loading) {
      console.log(
        `[ID:${invocationId}] Starting processing - setting isProcessingNextSteps=true`
      );
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
          response: {
            ...apiStatus.data?.response, // Spread the existing response object properties
            clarifications: clarificationResponses, // Replace the clarifications array within response
          },
          status: apiStatus.data?.status, // Include previous status
          goal: currentGoalPromptText, // Use the stored goal
          session: sessionId,
          user_role: role, // Add user_role
          staff_id: staffId, // Add staff_id
          // The top-level clarifications are now moved inside the response object
        };

        const fullUrlWithParams = `${fullUrl}?${params.toString()}`; // Construct URL with params for logging
        console.log(
          `[ID:${invocationId}] NEXT STEPS - Making POST request to:`,
          fullUrlWithParams
        );
        console.log(
          `[ID:${invocationId}] NEXT STEPS - Request body:`,
          requestBody
        );
        console.log(
          `[ID:${invocationId}] NEXT STEPS - clarificationResponses:`,
          clarificationResponses
        );
        console.log(
          `[ID:${invocationId}] POST body sent to /model_response:`,
          JSON.stringify(requestBody, null, 2)
        );

        const response = await fetch(fullUrl, {
          method: "POST", // Use POST for sending body
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
        });
        console.log(
          `[ID:${invocationId}] NEXT STEPS - POST returned response:`,
          response
        );

        if (!response.ok) {
          const errorData = await response
            .json()
            .catch(() => ({ error: `HTTP error: ${response.status}` }));
          console.log(
            `[ID:${invocationId}] NEXT STEPS - Error response:`,
            errorData
          );
          throw new Error(errorData.error || `HTTP error: ${response.status}`);
        }
        const responseData = await response.json();
        console.log(
          `[ID:${invocationId}] NEXT STEPS - Raw server response:`,
          responseData
        );
        console.log(
          `[ID:${invocationId}] NEXT STEPS - Setting apiStatus with data and loading=false`
        );
        setApiStatus({ data: responseData, loading: false, error: null });
        setIsProcessingNextSteps(false); // End processing indicator on success
        // Set state based on whether a non-null/undefined answer is available
        setIsFinalAnswerAvailable(responseData?.response?.answer != null);
        setClarificationResponses([]); // Clear clarification responses after successful submission
      } catch (err) {
        console.log(
          `[ID:${invocationId}] NEXT STEPS - Caught error:`,
          err.message
        );
        setApiStatus({
          data: apiStatus.data,
          loading: false,
          error: err.message,
        });
        setIsProcessingNextSteps(false); // End processing indicator on error
        setIsFinalAnswerAvailable(false); // Reset state on error
      }
    } else if (!statusUpdate.loading && apiStatus.loading) {
      setApiStatus({ ...statusUpdate, startTime: null });
    } else {
      setApiStatus((prevStatus) => ({ ...prevStatus, ...statusUpdate }));
    }
  };

  const handleLogin = (currentUsername, currentStaffId, currentRole) => {
    if (currentUsername && currentStaffId && currentRole) {
      setLoginMessage(`${currentUsername} you are now connected as ${currentRole} role with staff id ${currentStaffId}`);
      // Potentially switch view or perform other actions upon successful "login"
      // For now, just updates the message.
      // setActiveView("Question"); // Example: Switch to Question view after login
    } else if (!currentUsername) {
      setLoginMessage("User Name is required.");
    } else if (!currentStaffId) {
      setLoginMessage("Staff Id is required.");
    } else if (!currentRole) {
      setLoginMessage("Role is required.");
    }
     else {
      // This case might be redundant if individual checks are comprehensive
      // but can catch multiple missing fields.
      let missingFields = [];
      if (!currentUsername) missingFields.push("User Name");
      if (!currentStaffId) missingFields.push("Staff Id");
      if (!currentRole) missingFields.push("Role");
      setLoginMessage(`${missingFields.join(", ")} are required.`);
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
          {activeView === "Login" ? (
            <Grid item xs={12}> {/* Ensure LoginSection takes full width */}
              <LoginSection
                username={username}
                setUsername={setUsername}
                staffId={staffId}
                setStaffId={setStaffId}
                role={role}
                setRole={setRole}
                handleLogin={handleLogin}
                loginMessage={loginMessage}
              />
            </Grid>
          ) : (
            <>
              <Grid item xs={12}> {/* Changed from Grid xs={12} to Grid item xs={12} for clarity */}
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
                      isFinalAnswerAvailable={isFinalAnswerAvailable} // Pass the new prop
                      activityStatus={
                        isFinalAnswerAvailable
                          ? "Done"
                          : apiStatus.loading || isProcessingNextSteps
                          ? `thinking, please be patient [${elapsedSeconds}s]`
                          : ""
                      } // Pass activity status based on combined state
                      promptText={promptText} // Pass promptText state down
                      setPromptText={setPromptText} // Pass setPromptText function down
                    />
                  )}
                  {activeView === "Prompts" && (
                    <Box
                      sx={{
                        ...homePaper,
                        display: "flex",
                        flexDirection: "column",
                        gap: 2,
                        minHeight: '264px', // Set a minimum height for the container
                      }}
                    >
                      <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                        <TextField
                          label="Session ID"
                          value={sessionId} // Use the sessionId state
                          variant="outlined"
                          size="small" // Use small size
                          InputProps={{
                            readOnly: false, // Make it read-write
                            sx: {
                              fontFamily: "monospace", // Override font to monospace
                            },
                          }}
                          onChange={(e) => setSessionId(e.target.value)} // Add onChange handler to update sessionId state
                          sx={{
                            width: "350px", // Set width to match the other Session ID field
                            "& .MuiInputBase-root": {
                              fontSize: "0.875rem", // Smaller font size
                              fontFamily: "monospace", // Ensure monospace font for input
                            },
                          }}
                          title="Session Id"
                        />
                        <Button
                          variant="contained" // Use contained variant for consistency
                          onClick={handleGetPrompts} // Add click handler
                          size="small" // Use small size
                          disabled={isGettingPrompts} // Disable button when loading
                        >
                          {isGettingPrompts ? "Loading..." : "Get Prompts"}
                        </Button>
                        {promptVersions.length > 0 && (
                          <TextField
                            select
                            label="Version"
                            value={selectedPromptVersion}
                            onChange={handleVersionChange}
                            variant="outlined"
                            size="small" // Use small size
                            sx={{ width: "150px" }} // Adjust width as needed
                          >
                            {promptVersions.map((version) => (
                              <MenuItem key={version} value={version}>
                                {version}
                              </MenuItem>
                            ))}
                          </TextField>
                        )}
                      </Box>
                      {/* Display the selected prompt text using ReadOnlyPrompt */}
                      {selectedPromptText && (
                        <Box sx={{ flexGrow: 1 }}> {/* Add flexGrow to make it take available space */}
                          <ReadOnlyPrompt
                            label={`Prompt (Version: ${selectedPromptVersion})`}
                            value={selectedPromptText}
                          />
                        </Box>
                      )}
                      {/* Display the response message if no prompts are found or on error */}
                      {!selectedPromptText && promptsResponse && (
                        <TextField
                          label="Response"
                          value={promptsResponse}
                          variant="outlined"
                          fullWidth
                          multiline
                          rows={2} // Fixed height to 2 rows
                          InputProps={{
                            readOnly: true,
                          }}
                        />
                      )}
                    </Box>
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
              {/* Status component is conditionally rendered only if not in Login, Settings, or Prompts view */}
              {activeView !== "Login" && activeView !== "Settings" && activeView !== "Prompts" && (
                <Grid item> {/* Changed from Grid to Grid item for clarity */}
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
            </>
          )}
        </Grid>
      </Box>
    </ThemeProvider>
  );
}

export default App;
