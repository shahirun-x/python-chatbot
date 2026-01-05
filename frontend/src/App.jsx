/* frontend/src/App.jsx */
import React, { useState, useEffect } from 'react';
import ChatWindow from './components/ChatWindow';

function App() {
  // Check system preference or default to 'light'
  const [theme, setTheme] = useState('light');

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  // Apply the theme to the HTML body
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <div className="App" style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: '100vh',
      width: '100vw'
    }}>
      <ChatWindow theme={theme} toggleTheme={toggleTheme} />
    </div>
  );
}

export default App;