import React, { useState, useRef, useEffect } from 'react';
import './MainContent.css';

const API_URL = 'https://bank-ai-react-assistant.onrender.com';

function MainContent() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [error, setError] = useState(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    initializeSession();
  }, []);

  const initializeSession = async () => {
    try {
      console.log('Initializing session...');
      const response = await fetch(`${API_URL}/api/session/new`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`Failed to create session: ${response.status}`);
      }

      const data = await response.json();
      console.log('Session created:', data);
      setSessionId(data.session_id);
      
      setMessages([{
        id: 1,
        text: data.initial_message,
        sender: 'assistant',
        timestamp: new Date()
      }]);
      
      setError(null);
    } catch (err) {
      console.error('Session initialization error:', err);
      setError(`Failed to connect to the server. ${err.message}`);
      setMessages([{
        id: 1,
        text: "I'm having trouble connecting to the server. Please make sure the backend is running on http://localhost:8000",
        sender: 'assistant',
        timestamp: new Date()
      }]);
    } finally {
      setIsInitializing(false);
    }
  };

  const sendMessage = async (messageText) => {
    try {
      console.log('Sending message:', messageText);
      console.log('Session ID:', sessionId);
      console.log('Request URL:', `${API_URL}/api/chat`);

      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          session_id: sessionId
        }),
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log('Response data:', data);
      
      if (!sessionId) {
        setSessionId(data.session_id);
      }

      const assistantMessage = {
        id: messages.length + 2,
        text: data.response,
        sender: 'assistant',
        timestamp: new Date(data.timestamp)
      };

      setMessages(prev => [...prev, assistantMessage]);
      setError(null);
    } catch (err) {
      console.error('Send message error:', err);
      setError(`Failed to send message: ${err.message}`);
      
      const errorMessage = {
        id: messages.length + 2,
        text: "I'm sorry, I couldn't process your request. Please try again.",
        sender: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSend = () => {
    if (input.trim() === '' || isTyping) return;

    const userMessage = {
      id: messages.length + 1,
      text: input,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const messageToSend = input;
    setInput('');
    setIsTyping(true);

    sendMessage(messageToSend);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const resetSession = async () => {
    setIsInitializing(true);
    setMessages([]);
    setSessionId(null);
    setError(null);
    await initializeSession();
  };

  return (
    <div className="app">
      <div className="chat-container">
        <div className="chat-header">
          <div className="header-content">
            <div className="bank-logo">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21h18M3 10h18M3 7l9-4 9 4M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3" />
              </svg>
            </div>
            <div className="header-text">
              <h1>SecureBank Assistant</h1>
              <p className="status">
                {isInitializing ? 'Connecting...' : error ? 'Connection Error' : 'Online • Ready to help'}
              </p>
            </div>
            <button onClick={resetSession} className="reset-button" title="Start new conversation">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>

        <div className="messages-container">
          {error && (
            <div className="error-banner">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`message ${message.sender === 'user' ? 'user-message' : 'assistant-message'}`}
            >
              <div className="message-content">
                <div className="message-bubble">
                  {message.text}
                </div>
                <span className="message-time">{formatTime(message.timestamp)}</span>
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="message assistant-message">
              <div className="message-content">
                <div className="message-bubble typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here..."
              rows="1"
              disabled={isTyping || isInitializing}
            />
            <button 
              onClick={handleSend}
              disabled={input.trim() === '' || isTyping || isInitializing}
              className="send-button"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MainContent;