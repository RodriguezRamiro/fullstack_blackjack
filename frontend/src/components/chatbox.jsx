import { useState } from "react";
import '../styles/blackjackgame.css';


const Chatbox = () => {
    const [messages, setMessages] = useState([]);
    const [message, setMessage] = useState("");

    function handleSendMessage(e) {
      e.preventDefault();
      if (message.trim() !== "") {
        const newMsg = { user: "You", text: message };
        setMessages((prev) => [...prev, newMsg]);
        setMessage("");
      }
    }

    return (
      <div className="chatbox-container">
        <div className="chat-messages">
          {/* Use messages.map to render the messages */}
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