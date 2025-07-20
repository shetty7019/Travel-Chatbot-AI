import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (input.trim() === '') return;
    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    try {
      const response = await fetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage.content, session_id: sessionId }),
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      setSessionId(data.session_id);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.reply,
          timestamp: new Date().toLocaleTimeString(),
        }
      ]);
    } catch {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Oops! Something went wrong. Please try again.',
          timestamp: new Date().toLocaleTimeString(),
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') sendMessage();
  };

  return (
    <div className="travel-container">
      <div className="travel-header">
        Travel AI Assistant 
      </div>
      <div className="travel-messages">
        {messages.map((msg, idx) => (
          <div className={`message-bubble ${msg.role}`} key={idx}>
            <div className="message-text">{msg.content}</div>
            <div className="message-timestamp">{msg.timestamp}</div>
          </div>
        ))}
        {loading && <div className="loading-indicator">Travel AI Assistant is thinking...</div>}
        <div ref={messagesEndRef} />
      </div>
      <div className="travel-input-bar">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Type your question..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}

export default App;
