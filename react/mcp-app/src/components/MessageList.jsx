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
      
      // Add the message - no duplicate checking needed since backend only returns new messages
      if (data && (data.message || data.content)) {
        setMessages(prevMessages => {
          setActiveTab(tabIndex); // Switch to this tab when a new message arrives
          return [...prevMessages, data];
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
            {message.timestamp && message.message
              ? `${message.timestamp}: ${message.message}`
              : message.content
                ? `${message.timestamp || 'No timestamp'}: ${message.content}`
                : JSON.stringify(message, null, 2)
            }
          </div>
        ))}
      </div>
    </div>
  );
};

export default MessageList;