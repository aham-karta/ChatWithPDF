import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const App = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (input.trim()) {
      const userMessage = { text: input, sender: 'user' };
      setMessages([...messages, userMessage]);
      setInput('');
      try {
        const response = await axios.post('http://localhost:5000/api/generate', { query: input });
        const botMessage = { text: response.data, sender: 'bot' };
        setMessages((prevMessages) => [...prevMessages, botMessage]);
      } catch (error) {
        console.error('Error communicating with the bot:', error);
      }
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-900 text-white">
      <div className="chat-container bg-gray-800 rounded-lg shadow-lg flex flex-col h-4/5 w-8/12">
        <div className="chat-history overflow-y-auto px-4 py-2 flex-1">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`chat-message rounded-md p-2 ${
                msg.sender === 'user'
                  ? 'bg-blue-500 text-white self-end md:max-w-6/12 w-full rounded-xl mb-2'
                  : 'bg-gray-700 text-white self-start md:max-w-6/12 w-full rounded-xl mb-12'
              }`}
            >
              {msg.text}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        <div className="chat-input px-4 py-2 pb-4">
          <input
            type="text"
            className="flex-1 pl-2 w-11/12 h-12 bg-gray-700 rounded-l-md focus:outline-none placeholder-gray-400"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          />
          <button
            className="p-2 bg-blue-600 w-1/12 h-12 rounded-r-md hover:bg-blue-700 focus:outline-none"
            onClick={sendMessage}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default App;
