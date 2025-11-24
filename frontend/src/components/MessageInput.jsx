import React from 'react';
import './MessageInput.css';

const MessageInput = ({ input, setInput, sendMessage }) => {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="message-input-container">
      <textarea
        className="message-input"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about Python..."
      />
      <button className="send-button" onClick={sendMessage}>
        Send
      </button>
    </div>
  );
};

export default MessageInput;