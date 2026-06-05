import React, { useState, useRef, useEffect } from "react";
import { askReportQuestion } from "../api/chatApi";

const ReportChat = ({ reportId }) => {
  const [messages, setMessages] = useState([
    {
      sender: "ai",
      text: "Hello! You can ask questions about your lab reports as well as general health and medical topics. I will explain things in simple language (this is not a diagnosis).",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = { sender: "user", text: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await askReportQuestion({
        report_id: reportId,
        question: userMsg.text,
      });
      setMessages((msgs) => [
        ...msgs,
        { sender: "ai", text: res.data.answer || "No answer received." },
      ]);
    } catch (error) {
      console.error("Report chat error:", error);
      setMessages((msgs) => [
        ...msgs,
        { sender: "ai", text: "Sorry, there was an error getting a response." },
      ]);
    }
    setLoading(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !loading) sendMessage();
  };

  return (
    <div className="flex flex-col h-[70vh] max-w-2xl mx-auto bg-white rounded shadow p-4">
      <div className="flex-1 overflow-y-auto mb-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"} mb-2`}
          >
            <div
              className={`px-4 py-2 rounded-lg max-w-[70%] text-sm ${
                msg.sender === "user"
                  ? "bg-blue-600 text-white self-end"
                  : "bg-gray-200 text-gray-800 self-start"
              }`}
            >
              {msg.sender === "ai" ? (
                <span style={{ whiteSpace: "pre-line" }}>{msg.text}</span>
              ) : (
                msg.text
              )}
            </div>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>
      <div className="flex items-center gap-2">
        <input
          type="text"
          className="flex-1 border rounded px-3 py-2 focus:outline-none focus:ring"
          placeholder="Type your question..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="bg-blue-600 text-white px-4 py-2 rounded font-semibold hover:bg-blue-700 transition"
        >
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
};

export default ReportChat;
