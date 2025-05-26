import React, { useEffect, useState, useRef } from 'react';
import '../styles/blackjackgame.css';

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
      if (data.isglobal) return;  // skip global messages
      if (tableId && data.tableId !== tableId) return;
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

    if (!tableId) {
      return <div>Loading chat room...</div>;  // or some other placeholder
    }

    socket.emit("chat_message", {
      tableId,
      playerId,
      username,
      message: input.trim(),
    });

    setInput('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') sendMessage();
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  console.log('RoomChat props:', { tableId, playerId, username });

  useEffect(() => {
    console.log('tableId changed:', tableId);
  }, [tableId]);


  return (
    <div className="chatbox">
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx}><strong>{msg.username}:</strong> {msg.message}</div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyPress}
        placeholder="Type a message..."
        disabled={!tableId}
      />
      <button onClick={sendMessage} disabled={!input.trim() || !tableId}>
        Send
      </button>

    </div>
  );
};

export default RoomChat;
