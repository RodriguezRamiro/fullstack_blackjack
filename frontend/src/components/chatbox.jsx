// chatbox.jsx

import { useEffect, useState } from "react";

const Chatbox = ({ socket, tableId, playerId, username }) => {
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState("");

  // Only listen for incoming messages
  useEffect(() => {
    if (!socket) return;


    const handleChatMessage = (msg) => {
      console.log("Received message:", msg);
      setMessages((prev) => [...prev, msg]);
    };

    socket.on("chat_message", handleChatMessage);

    return () => {
      socket.off("chat_message", handleChatMessage);
    };
  }, [socket]);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!message.trim() || !socket) return;

    const newMsg = { tableId, playerId, username, message };
    console.log("About to emit chat_message:", newMsg);
    socket.emit("chat_message", newMsg);
    console.log("chat_message emitted!")
    setMessage("");
  };



  return (
    <div className="chatbox-container">
      <div className="chatbox-header">Chat</div>
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx}>
            <strong>{msg.username}:</strong> {msg.message}
          </div>
        ))}
      </div>
      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          placeholder="Type your message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="chat-input"
        />
        <button type="submit" className="chat-send-btn">Send</button>
      </form>
    </div>
  );
};

export default Chatbox;
