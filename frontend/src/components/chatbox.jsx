// chatbox.jsx

import { useEffect, useState } from "react";


const Chatbox = ({ socket, tableId, playerId, username }) => {
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!socket || !tableId || !playerId || !username) return;

    console.log("Emitting join from chatbox")
    socket.emit("join", {
      tableId,
      playerId,
      username,

    });

    socket.on("chat_message", (msg) => {
      console.log("Received message:", msg);
      setMessages((prev) => [...prev, msg]);
    });

    return () => {
      socket.off("chat_message");
    };
  }, [socket, tableId, playerId, username]);

  const handleSendMessage = (e) => {
    e.preventDefault();
    console.log("sending Message"); // debug log
    if (!message.trim() || !socket) return;

    const newMsg = { tableId, playerId, username, message };
    socket.emit("chat_message", newMsg);
    setMessages((prev) => [...prev, newMsg]);
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