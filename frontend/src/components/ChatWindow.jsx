import React, { useState, useEffect, useRef } from 'react';
import './ChatWindow.css';
import MessageList from './MessageList';
import MessageInput from './MessageInput';

const ChatWindow = () => {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hello! How can I help you with Python today?' }
  ]);
  const [input, setInput] = useState('');
  // We don't need to manage session_id on the frontend for this version,
  // the backend handles creating it. We will just send what we have.
  const [session_id, setSessionId] = useState(null); 

  const messagesEndRef = useRef(null);
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (input.trim() === '') return;

    const userMessage = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    
    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input, session_id: session_id }),
      });

      if (!response.ok) throw new Error('Network response was not ok');
      if (!response.body) throw new Error("Response body is null");

      // Read the session_id from the header
      const newSessionId = response.headers.get('X-Session-Id');
      if (newSessionId && !session_id) {
        setSessionId(newSessionId);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      setMessages(prev => [...prev, { sender: 'bot', text: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        
        // THIS IS THE CORRECT, IMMUTABLE WAY TO UPDATE THE LAST MESSAGE
        setMessages(prev => {
            // Make a copy of the messages array
            const newMessages = [...prev];
            // Get the last message
            const lastMessage = newMessages[newMessages.length - 1];
            // Create a *new* object for the last message with the updated text
            newMessages[newMessages.length - 1] = {
                ...lastMessage,
                text: lastMessage.text + chunk,
            };
            return newMessages;
        });
      }

    } catch (error) {
      console.error('Error fetching response:', error);
      const errorMessage = { sender: 'bot', text: 'Sorry, I ran into an error. Please try again.' };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <h2>Python Tutor</h2>
      </div>
      <div className="chat-body">
        <MessageList messages={messages} />
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-footer">
        <MessageInput input={input} setInput={setInput} sendMessage={sendMessage} />
      </div>
    </div>
  );
};

export default ChatWindow;