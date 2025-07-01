import React, { useState, useEffect } from 'react';
import './MessageList.css'; // Import the CSS file

const MessageList = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [messagesTab1, setMessagesTab1] = useState([]);
  const [messagesTab2, setMessagesTab2] = useState([]);
  const [messagesTab3, setMessagesTab3] = useState([]);
  const [lastFetchTime, setLastFetchTime] = useState({});
  const [fetchErrors, setFetchErrors] = useState({});

  const tabs = [
    {
      id: 1,
      name: 'Trading',
      url: 'http://localhost:5174/get_message?channel_id=e2342e61-2926-44ec-9e75-7e8e815a7f5c',
      messages: messagesTab1,
      setMessages: setMessagesTab1
    },
    {
      id: 2,
      name: 'Support',
      url: 'http://localhost:5174/get_message?channel_id=5d6581c4-e928-44db-ab80-12e805434180',
      messages: messagesTab2,
      setMessages: setMessagesTab2
    },
    {
      id: 3,
      name: 'Ops & Finance',
      url: 'http://localhost:5174/get_message?channel_id=6a6dc996-e2ad-4b27-9d4a-aa6c77532b24',
      messages: messagesTab3,
      setMessages: setMessagesTab3
    }
  ];

  const fetchMessage = async (url, setMessages, tabIndex) => {
    const now = new Date().toISOString();
    setLastFetchTime(prev => ({ ...prev, [tabIndex]: now }));
    
    try {
      console.log(`Tab ${tabIndex} making blocking call to: ${url}`);
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log(`Tab ${tabIndex} received data:`, data);
      
      // Clear any previous errors for this tab
      setFetchErrors(prev => ({ ...prev, [tabIndex]: null }));
      
      // Add the message(s) - handle both single message and multiple messages
      if (data && (data.message || data.content || data.messages)) {
        setMessages(prevMessages => {
          setActiveTab(tabIndex); // Switch to this tab when a new message arrives
          
          // If data contains multiple messages (messages array)
          if (data.messages && Array.isArray(data.messages)) {
            return [...prevMessages, ...data.messages];
          }
          // If data contains a single message
          else {
            return [...prevMessages, data];
          }
        });
      }
    } catch (error) {
      console.error(`Fetching message failed for tab ${tabIndex}:`, error);
      setFetchErrors(prev => ({ ...prev, [tabIndex]: error.message }));
      throw error; // Re-throw to trigger retry logic
    }
  };

  useEffect(() => {
    console.log('MessageList component mounted with tabs:', tabs.length);
    
    // Track active fetches to prevent multiple requests per tab
    const activeFetches = new Set();
    let isMounted = true;
    
    // Start blocking fetch for each tab
    const startBlockingFetch = async (tab, index) => {
      if (activeFetches.has(index)) {
        console.log(`Tab ${index} already has active fetch, skipping`);
        return;
      }
      
      activeFetches.add(index);
      
      while (isMounted) {
        try {
          console.log(`Tab ${index} starting blocking fetch...`);
          await fetchMessage(tab.url, tab.setMessages, index);
          console.log(`Tab ${index} received response, starting next fetch...`);
        } catch (error) {
          console.error(`Blocking fetch error for tab ${index}:`, error);
          if (isMounted) {
            // Wait before retrying on error
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
        }
      }
      
      activeFetches.delete(index);
    };

    // Start blocking fetch for each tab
    tabs.forEach((tab, index) => {
      startBlockingFetch(tab, index);
    });

    // Cleanup function
    return () => {
      isMounted = false;
      console.log('MessageList unmounting, stopping all fetches');
    };
  }, []);

  const handleTabClick = (tabIndex) => {
    setActiveTab(tabIndex);
  };

  const currentTab = tabs[activeTab];

  return (
    <div className="message-list-wrapper">
      <div className="tab-container">
        {tabs.map((tab, index) => (
          <button
            key={tab.id}
            className={`tab-button ${activeTab === index ? 'active' : ''}`}
            onClick={() => handleTabClick(index)}
            title={`${tab.name} - Messages: ${tab.messages.length}${fetchErrors[index] ? ` - Error: ${fetchErrors[index]}` : ''}`}
          >
            {tab.name} ({tab.messages.length})
            {fetchErrors[index] && <span style={{color: 'red'}}> ⚠</span>}
          </button>
        ))}
      </div>
      <div className="message-list-container">
        {currentTab.messages.length === 0 && (
          <div className="message-item" style={{color: '#888', fontStyle: 'italic'}}>
            No messages yet...
            {lastFetchTime[activeTab] && ` (Last fetch: ${new Date(lastFetchTime[activeTab]).toLocaleTimeString()})`}
            {fetchErrors[activeTab] && ` - Error: ${fetchErrors[activeTab]}`}
          </div>
        )}
        {currentTab.messages.map((message, index) => (
          <div key={index} className="message-item">
            {(() => {
              // Handle different message formats
              if (typeof message === 'string') {
                return message;
              }
              
              // If message has timestamp and message fields
              if (message.timestamp && message.message) {
                // Check if message.message is an object with nested message content
                if (typeof message.message === 'object' && message.message.message) {
                  // Extract the actual message content from the nested structure
                  return `${message.timestamp}: ${message.message.message}`;
                }
                // If message.message is a simple string
                else if (typeof message.message === 'string') {
                  return `${message.timestamp}: ${message.message}`;
                }
                // If message.message is an object but doesn't have .message property
                else if (typeof message.message === 'object') {
                  return `${message.timestamp}: ${JSON.stringify(message.message)}`;
                }
              }
              
              // If message has timestamp and content fields
              if (message.content) {
                return `${message.timestamp || 'No timestamp'}: ${message.content}`;
              }
              
              // If message is an object but doesn't have expected structure,
              // try to extract the message content intelligently
              if (typeof message === 'object' && message !== null) {
                // Check if it's a nested message object
                if (message.message && typeof message.message === 'object') {
                  const innerMessage = message.message;
                  if (innerMessage.message) {
                    return `${message.timestamp || innerMessage.timestamp || 'No timestamp'}: ${innerMessage.message}`;
                  }
                  if (innerMessage.content) {
                    return `${message.timestamp || innerMessage.timestamp || 'No timestamp'}: ${innerMessage.content}`;
                  }
                }
                
                // Fallback to JSON stringify for debugging
                return JSON.stringify(message, null, 2);
              }
              
              return 'Invalid message format';
            })()}
          </div>
        ))}
      </div>
    </div>
  );
};

export default MessageList;