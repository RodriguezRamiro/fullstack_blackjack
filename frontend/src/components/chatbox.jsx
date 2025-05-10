// chatbox.jsx
import { useEffect, useState } from "react";
import { io } from "socket.io-client";
import '../styles/blackjackgame.css';

const socket = io('http://localhost:5001'); // adjust if needed for deployment

const Chatbox = () => {
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState("");

  useEffect(() => {
    // Listen for incoming messages from server
    socket.on("message", (msg) => {
      setMessages((prev) => [...prev, { user: "Other", text: msg }]);
    });

    return () => {
      socket.off("message");
    };
  }, []);

  function handleSendMessage(e) {
    e.preventDefault();
    if (message.trim() !== "") {
      const newMsg = { user: "You", text: message };
      setMessages((prev) => [...prev, newMsg]);
      socket.emit("message", message); // Send to server
      setMessage("");
    }
  }

  return (
    <div className="chatbox-container" id="chatbox">
      <div className="chatbox-header">Chat</div>
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx}>
            <strong>{msg.user}:</strong> {msg.text}
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
