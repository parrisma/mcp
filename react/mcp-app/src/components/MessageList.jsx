import React, { useState, useEffect } from 'react';
import './MessageList.css'; // Import the CSS file

const MessageList = () => {
  const [messages, setMessages] = useState([]);
  const url = 'http://localhost:5174/get_message?channel_id=e2342e61-2926-44ec-9e75-7e8e815a7f5c';

  const fetchMessage = async () => {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setMessages(prevMessages => [...prevMessages, data]);
      // Fetch the next message immediately after receiving one
      fetchMessage();
    } catch (error) {
      console.error("Fetching message failed:", error);
      // Optionally, add a delay before retrying on error
      setTimeout(fetchMessage, 5000); // Retry after 5 seconds
    }
  };

  useEffect(() => {
    fetchMessage();
  }, []); // Empty dependency array means this effect runs once on mount

  return (
    <div className="message-list-container">
      {messages.map((message, index) => (
        <div key={index} className="message-item">
          {`${message.timestamp}: ${message.message}`}
        </div>
      ))}
    </div>
  );
};

export default MessageList;