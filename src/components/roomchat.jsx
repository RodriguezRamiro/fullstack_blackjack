//src/components/roomchat.jsx

import React, { useEffect, useState, useRef } from 'react';
import '../styles/blackjackgame.css';


// Simple avatar function, replace or extend as needed
const getAvatarUrl = (username) => {
  if (!username) return '/avatars/default.png'; // fallback avatar URL
  // Use ui-avatars for quick placeholder avatars:
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(username)}&background=random&color=fff`;
};


const RoomChat = ({ socket, tableId, playerId, username }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (!socket) {
      console.log("Socket is undefined in Chatbox");
      return;
    }

    const handleMessage = (data) => {
      console.log("[RoomChat] Received chat_message:", data);
      if (data.isglobal) return; // Skip global messages
      if (tableId && data.tableId !== tableId) return;
      console.log("Local tableId:", tableId, "Message tableId:", data.tableId);
      if (!tableId && data.tableId) return;
      setMessages((prev) => [...prev, data]);
    };

    socket.on("chat_message", handleMessage);
    return () => socket.off("chat_message", handleMessage);
  }, [socket, tableId]);

  const sendMessage = () => {
    console.log("sendMessage called with:", { tableId, playerId, username, input });

    if (!input.trim() || !socket) {
      console.log("Socket or input is missing.");
      return;
    }

    if (!tableId || !playerId || !username) {
      console.warn("Missing required chat info", { tableId, playerId, username });
      return;
    }

    socket.emit("chat_message", {
      tableId,
      playerId,
      username,
      message: input.trim(),
      isGlobal: false,
    });

    setInput('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') sendMessage();
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chatbox-container">
      <div className="chat-messages">
        {messages.map((msg, idx) => {
          const isSelf = msg.username === username;
          const isDealer = !msg.username || msg.username.toLowerCase() == 'dealer';
          const displayName = isSelf ? 'You' : msg.username || 'Dealer';

          //For avatar
          const avatarUrl = getAvatarUrl(msg.username);

          return (
            <div
        key={idx}
        className={`chat-message room ${isSelf ? 'self' : isDealer ? 'dealer' : 'other'}`}
        style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '8px' }}>
          <img
          src={avatarUrl}
          alt={`${displayName} avatar`}
          className="chat-avatar"
          style={{ width: 40, height: 40, borderRadius: '50%', marginRight: 8 }}
        />
        <div className={`chat-bubble ${isSelf ? 'bubble-self' : 'bubble-other'}`}>
          <div className="chat-username" style={{ fontWeight: 'bold', marginBottom: 4 }}>
            {displayName}
            </div>
          <div>{msg.message}</div>
        </div>
      </div>
    );
  })}
  <div ref={messagesEndRef} />
</div>
      <form
        className="chat-input-form"
        onSubmit={(e) => {
          e.preventDefault();
          sendMessage();
        }}
      >
        <input
          type="text"
          className="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder="Type a message..."
          disabled={!tableId}
        />
        <button
          type="submit"
          className="chat-send-btn"
          disabled={!input.trim() || !tableId}
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default RoomChat;
