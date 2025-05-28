import React from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import MCPServerCard from "./MCPServerCard"; // Import the new component

function SettingsAndStatus() {
  const clientHost = "localhost";
  const llmModel = "9312";

  const [clientHostValue, setClientHostValue] = React.useState(clientHost);
  const [clientPortValue, setClientPortValue] = React.useState(llmModel);

  const [pingResult, setPingResult] = React.useState(null);
  const [pingLoading, setPingLoading] = React.useState(false);
  const [pingError, setPingError] = React.useState(null);

  // State for config values
  const [mcpHostDisplayValue, setMcpHostDisplayValue] = React.useState(
    "Press Get Config..."
  );
  const [ollamaHostDisplayValue, setOllamaHostDisplayValue] = React.useState(
    "Press Get Config..."
  );
  const [ollamaModelDisplayValue, setOllamaModelDisplayValue] = React.useState(
    "Press Get Config..."
  );

  const [configLoading, setConfigLoading] = React.useState(false);
  const [configError, setConfigError] = React.useState(null);

  // State for MCP Servers list
  const [mcpServersList, setMcpServersList] = React.useState([]);
  const [mcpServersLoading, setMcpServersLoading] = React.useState(false);
  const [mcpServersError, setMcpServersError] = React.useState(null);

  const handlePing = async () => {
    setPingLoading(true);
    setPingError(null);
    setPingResult(null);
    try {
      const url = `http://${clientHostValue}:${clientPortValue}/ping`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }
      const data = await response.json();
      setPingResult(data);
    } catch (err) {
      setPingError(err.message);
    } finally {
      setPingLoading(false);
    }
  };

  const formatPingDate = (ping) => {
    if (!ping) return "";
    // Format: YYYY-MM-DD HH:mm:ss TZ
    const { year, month, day, hour, minute, second, timezone } = ping;
    const pad = (n) => n.toString().padStart(2, "0");
    return `${year}-${pad(month)}-${pad(day)} ${pad(hour)}:${pad(minute)}:${pad(
      second
    )} ${timezone}`;
  };

  const handleGetConfig = async () => {
    setConfigLoading(true);
    setConfigError(null);
    try {
      const url = `http://${clientHostValue}:${clientPortValue}/config`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }
      const data = await response.json();
      if (data.mcp_host_urls && data.mcp_host_urls.length > 0) {
        setMcpHostDisplayValue(data.mcp_host_urls[0]);
      }
      if (data.ollama_host_url) {
        setOllamaHostDisplayValue(data.ollama_host_url);
      }
      if (data.ollama_model_name) {
        setOllamaModelDisplayValue(data.ollama_model_name);
      }
    } catch (err) {
      setConfigError(err.message);
      // Optionally, display this error to the user
      console.error("Failed to fetch config:", err.message);
    } finally {
      setConfigLoading(false);
    }
  };

  const handleGetMcpServers = async () => {
    setMcpServersLoading(true);
    setMcpServersError(null);
    setMcpServersList([]); // Clear previous list
    try {
      const url = `http://${clientHostValue}:${clientPortValue}/capability`;
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }
      const data = await response.json();
      // The data is an object where keys are server names
      // We need to transform it into an array of objects for MCPServerCard
      // Each item in the array will be an object with a single key (server name)
      // and its value will be the server's capability data.
      const serversArray = Object.entries(data).map(([serverName, serverData]) => ({
        [serverName]: serverData,
      }));
      setMcpServersList(serversArray);
    } catch (err) {
      setMcpServersError(err.message);
      console.error("Failed to fetch MCP servers:", err.message);
    } finally {
      setMcpServersLoading(false);
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 2,
        padding: 2,
        border: "1px solid grey",
        borderRadius: "4px",
      }}
    >
      {/* First row */}
      {/* Main 3-column layout */}
      <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 2 }}>
        {/* Column 1: Client Host, Client Port, URL */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <TextField
            label="Client Host"
            variant="outlined"
            size="small"
            value={clientHostValue}
            onChange={(e) => setClientHostValue(e.target.value)}
            sx={{
              width: "100%", // Use full width of column
              "& .MuiInputBase-input": {
                fontSize: "0.875rem",
              },
            }}
          />
          <TextField
            label="Client Port"
            variant="outlined"
            size="small"
            value={clientPortValue}
            onChange={(e) => setClientPortValue(e.target.value)}
            sx={{
              width: "100%",
              "& .MuiInputBase-input": {
                fontSize: "0.875rem",
              },
            }}
          />
        </Box>

        {/* Column 2: URL, Ping functionality */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <TextField
            label="URL"
            variant="outlined"
            size="small"
            value={`http://${clientHostValue}:${clientPortValue}`}
            readOnly={true}
            sx={{
              width: "100%",
              "& .MuiInputBase-input": {
                color: "#757575",
                fontSize: "0.875rem",
              },
              "&:hover .MuiOutlinedInput-notchedOutline": {
                borderColor: "rgba(0, 0, 0, 0.23)",
              },
            }}
          />
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <button
              onClick={handlePing}
              disabled={pingLoading}
              style={{
                padding: "4px 12px",
                borderRadius: 4,
                border: "1px solid #1976d2",
                background: "#1976d2",
                color: "#fff",
                cursor: pingLoading ? "not-allowed" : "pointer",
              }}
            >
              {pingLoading ? "Pinging..." : "Ping"}
            </button>
            <TextField
              label="Ping Status"
              variant="outlined"
              size="small"
              readOnly={true}
              value={
                pingLoading
                  ? "Pinging..."
                  : pingError
                  ? `Error: ${pingError}`
                  : pingResult && pingResult.ping
                  ? formatPingDate(pingResult.ping)
                  : "Press Ping..."
              }
              sx={{
                flexGrow: 1, // Allow TextField to take remaining space
                minWidth: 180, // Ensure it has some minimum width
                "& .MuiInputBase-input": {
                  color: "#757575",
                  fontSize: "0.875rem",
                },
                "& .MuiInputLabel-root": {
                  fontSize: "0.875rem",
                },
                "&:hover .MuiOutlinedInput-notchedOutline": {
                  borderColor: "rgba(0, 0, 0, 0.23)",
                },
              }}
            />
          </Box>
        </Box>

        {/* Column 3: Get Config, MCP Host, Ollama Host, Ollama Model */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-start",
              gap: 1,
            }}
          >
            <button
              onClick={handleGetConfig}
              disabled={configLoading}
              style={{
                padding: "4px 12px",
                borderRadius: 4,
                border: "1px solid #1976d2",
                background: "#1976d2",
                color: "#fff",
                cursor: configLoading ? "not-allowed" : "pointer",
              }}
            >
              {configLoading ? "Fetching..." : "Get Config"}
            </button>
            {configError && (
              <Typography
                variant="caption"
                color="error"
                sx={{ fontSize: "0.75rem" }}
              >
                Error: {configError}
              </Typography>
            )}
          </Box>
          <TextField
            label="MCP Host"
            variant="outlined"
            size="small"
            value={mcpHostDisplayValue}
            readOnly={true}
            sx={{
              width: "100%",
              "& .MuiInputBase-input": {
                color: "#757575",
                fontSize: "0.875rem",
              },
              "&:hover .MuiOutlinedInput-notchedOutline": {
                borderColor: "rgba(0, 0, 0, 0.23)",
              },
            }}
          />
          <TextField
            label="Ollama Host"
            variant="outlined"
            size="small"
            value={ollamaHostDisplayValue}
            readOnly={true}
            sx={{
              width: "100%",
              "& .MuiInputBase-input": {
                color: "#757575",
                fontSize: "0.875rem",
              },
              "&:hover .MuiOutlinedInput-notchedOutline": {
                borderColor: "rgba(0, 0, 0, 0.23)",
              },
            }}
          />
          <TextField
            label="Ollama Model"
            variant="outlined"
            size="small"
            value={ollamaModelDisplayValue}
            readOnly={true}
            sx={{
              width: "100%",
              "& .MuiInputBase-input": {
                color: "#757575",
                fontSize: "0.875rem",
              },
              "&:hover .MuiOutlinedInput-notchedOutline": {
                borderColor: "rgba(0, 0, 0, 0.23)",
              },
            }}
          />
        </Box>
      </Box>

      {/* Fourth Row: MCP Servers Display Area */}
      <Box sx={{ mt: 2, border: "1px dashed grey", borderRadius: "4px", p: 1 }}>
        <Box sx={{ display: "flex", justifyContent: "flex-start", alignItems: "center", mb: 1 }}>
          {/* Button and error message container, aligned to the left */}
          <Box sx={{display: "flex", alignItems: "center", gap: 1 }}>
            <button
              onClick={handleGetMcpServers}
              disabled={mcpServersLoading}
              style={{
                padding: "4px 12px",
                borderRadius: 4,
                border: "1px solid #1976d2",
                background: "#1976d2",
                color: "#fff",
                cursor: mcpServersLoading ? "not-allowed" : "pointer",
              }}
            >
              {mcpServersLoading ? "Fetching Servers..." : "Get MCP Servers"}
            </button>
            {mcpServersError && (
              <Typography variant="caption" color="error" sx={{ fontSize: '0.75rem' }}>
                Error: {mcpServersError}
              </Typography>
            )}
          </Box>
        </Box>
        <Box
          sx={{
            maxHeight: "400px", // Max height before scrolling
            overflowY: "auto", // Enable vertical scroll
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))", // Responsive grid
            gap: 2, // Gap between cards
            p: 1, // Padding for the content area
          }}
        >
          {mcpServersList.length > 0 ? (
            mcpServersList.map((serverData, index) => (
              <MCPServerCard key={index} jsonData={serverData} />
            ))
          ) : (
            !mcpServersLoading && !mcpServersError && (
              <Typography sx={{gridColumn: '1 / -1', textAlign: 'center', color: 'text.secondary'}}>
                Press "Get MCP Servers" to load server capabilities.
              </Typography>
            )
          )}
        </Box>
      </Box>
    </Box>
  );
}

export default SettingsAndStatus;
