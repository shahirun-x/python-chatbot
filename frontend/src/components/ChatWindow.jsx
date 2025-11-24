import React, { useState, useEffect, useRef } from 'react';
import './ChatWindow.css';
import MessageList from './MessageList';
import MessageInput from './MessageInput';

const ChatWindow = () => {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hello! How can I help you with Python today?' }
  ]);
  const [input, setInput] = useState('');
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
      // FIXED: Added "/api/chat" to the end of the URL
      const response = await fetch('https://improved-funicular-wrjgrrq755ww256gp-8000.app.github.dev/api/chat', {
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
        
        setMessages(prev => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
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