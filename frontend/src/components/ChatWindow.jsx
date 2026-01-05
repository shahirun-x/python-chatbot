/* frontend/src/components/ChatWindow.jsx */
import React, { useState, useEffect, useRef } from 'react';
import './ChatWindow.css';
import MessageList from './MessageList';
import MessageInput from './MessageInput';

const ChatWindow = ({ theme, toggleTheme }) => {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hello! I am your Python Assistant. How can I help you code today?' }
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
      const response = await fetch('https://shahirun-python-chatbot-backend.hf.space/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input, session_id: session_id }),
      });

      if (!response.ok) throw new Error('Network response was not ok');
      const newSessionId = response.headers.get('X-Session-Id');
      if (newSessionId && !session_id) setSessionId(newSessionId);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      setMessages(prev => [...prev, { sender: 'bot', text: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        setMessages(prev => {
            const newMessages = [...prev];
            const lastMsg = newMessages[newMessages.length - 1];
            newMessages[newMessages.length - 1] = { ...lastMsg, text: lastMsg.text + chunk };
            return newMessages;
        });
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { sender: 'bot', text: 'Sorry, I encountered an error.' }]);
    }
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <div className="header-title">
            <h2>Python Tutor</h2>
            <span className="status-dot"></span>
        </div>
        <button onClick={toggleTheme} className="theme-toggle" aria-label="Toggle Theme">
          {theme === 'light' ? '🌙' : '☀️'}
        </button>
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