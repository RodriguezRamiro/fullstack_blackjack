// GlobalChatBox.js (chat before joining a room)

import React, { useEffect, useState, useRef } from "react";
import socket from "../socket"; //


function GlobalChat({ username }) {
  const [message, setMessage] = useState("");
  const [chatLog, setChatLog] = useState([]);
  const chatEndRef = useRef(null);

  useEffect(() => {
    socket.on("chat_message", (data) => {
      if (data.isglobal) {
        setChatLog((prev) => [...prev, data]);
      }
    });

    return () => {
      socket.off("chat_message");
    };
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatLog]);

  const sendMessage = () => {
    const trimmed = message.trim();
    if (trimmed === "") return;

    socket.emit("chat_message", {
      username,
      message: trimmed,
      isglobal: true,
    });

    setMessage("");
  };

  return (
    <div className="global-chat">
      <div className="chat-log" style={{ maxHeight: "200px", overflowY: "auto" }}>
        {chatLog.map((msg, i) => (
          <div key={i}>
            <strong>{msg.username}:</strong> {msg.message}
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>
      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type a message..."
      />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
}


export default GlobalChat;
