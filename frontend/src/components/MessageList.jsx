import React from 'react';
import './MessageList.css';
import ReactMarkdown from 'react-markdown'; // Corrected import

const MessageList = ({ messages }) => {
  return (
    <div className="message-list">
      {messages.map((msg, index) => (
        <div key={index} className={`message ${msg.sender}`}>
          <ReactMarkdown>{msg.text}</ReactMarkdown>
        </div>
      ))}
    </div>
  );
};

export default MessageList;