import React, { useState, useEffect } from 'react';
import './MessageList.css'; // Import the CSS file

const MessageList = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [messagesTab1, setMessagesTab1] = useState([]);
  const [messagesTab2, setMessagesTab2] = useState([]);
  const [messagesTab3, setMessagesTab3] = useState([]);

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
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log(`Switching to tab ${tabIndex} for message:`, data);
      setMessages(prevMessages => [...prevMessages, data]);
      setActiveTab(tabIndex); // Switch to this tab when a message arrives
      // Fetch the next message immediately after receiving one
      fetchMessage(url, setMessages, tabIndex);
    } catch (error) {
      console.error("Fetching message failed:", error);
      // Optionally, add a delay before retrying on error
      setTimeout(() => fetchMessage(url, setMessages, tabIndex), 5000); // Retry after 5 seconds
    }
  };

  useEffect(() => {
    console.log('MessageList component mounted with tabs:', tabs.length);
    // Start fetching for all tabs
    tabs.forEach((tab, index) => {
      console.log(`Starting fetch for tab ${index} with URL:`, tab.url);
      fetchMessage(tab.url, tab.setMessages, index);
    });
  }, []); // Empty dependency array means this effect runs once on mount

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
          >
            {tab.name}
          </button>
        ))}
      </div>
      <div className="message-list-container">
        {currentTab.messages.map((message, index) => (
          <div key={index} className="message-item">
            {`${message.timestamp}: ${message.message}`}
          </div>
        ))}
      </div>
    </div>
  );
};

export default MessageList;