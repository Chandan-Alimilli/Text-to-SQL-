import React, { useEffect, useRef, useState } from "react";

import GroupIcon from "@mui/icons-material/Group";
import BusinessIcon from "@mui/icons-material/Business";
import PersonIcon from "@mui/icons-material/Person";
import StorageIcon from "@mui/icons-material/Storage";
import MicIcon from "@mui/icons-material/Mic";
import SendIcon from "@mui/icons-material/Send";
import logo from "./imgs/chase1.png";
import chase from "./imgs/chase.png";
import { useNavigate } from "react-router-dom";
import InsightsIcon from "@mui/icons-material/Insights";
import LocationCityIcon from "@mui/icons-material/LocationCity";
import TuneIcon from "@mui/icons-material/Tune";
import TextFieldsIcon from "@mui/icons-material/TextFields";
import PieChartIcon from "@mui/icons-material/PieChart";
import TableChartIcon from "@mui/icons-material/TableChart";
import ChartRenderer from "./ChartRenderer";
import TableRenderer from "./TableRenderer";
import BarChartIcon from "@mui/icons-material/BarChart";
import { motion } from "framer-motion";

const suggestions = [
  { text: "show all customer names and branch location.", icon: <GroupIcon /> },
  { text: "List all branch locations.", icon: <LocationCityIcon /> },
  {
    text: "Show customer names with their transaction amounts.",
    icon: <PersonIcon />,
  },
  { text: "What is the total number of branches?", icon: <StorageIcon /> },
  { text: "Get customer email and branch location", icon: <GroupIcon /> },
  {
    text: "show all transaction amounts and customer names",
    icon: <BusinessIcon />,
  },
  {
    text: "List all customers with their branch names and emails.",
    icon: <PersonIcon />,
  },
  { text: "Show average staff count per branch.", icon: <GroupIcon /> },
  {
    text: "show all customer spent amount and categories",
    icon: <PieChartIcon />,
  },
  {
    text: "show all customers by their customer names",
    icon: <TextFieldsIcon />,
  },

  { text: "Which branch generated the most revenue?", icon: <BusinessIcon /> },
];

export default function Chatbox() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [toolType, setToolType] = useState("text");
  const [toolOpen, setToolOpen] = useState(false);
  const [lastBotText, setLastBotText] = useState("");
  const [getSQLQuery, setGetSQLQuery] = useState(true);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [firstUserMessageSent, setFirstUserMessageSent] = useState(false);

  const chatRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (chatRef.current)
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages]);

  const sendMessage = async (msg) => {
    if (!msg.trim()) return;
    setMessages((prev) => [...prev, { type: "outgoing", text: msg }]);
    setInput("");
    setLoading(true);
    setFirstUserMessageSent(true);

    try {
      const endpoint = getSQLQuery ? "query" : "data"; // Important: reversed
      const res = await fetch(`http://localhost:8000/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: msg }),
      });

      const data = await res.json();
      const sql = data.sql || null;
      const resultData = data.response;
      const newMessages = [];

      if (getSQLQuery) {
        // ONLY show SQL query from /query
        newMessages.push({
          type: "incoming",
          isSqlQuery: true,
          heading: "SQL query generated successfully",
          text: sql || "N/A",
        });
      } else {
        // Show BOTH query and data from /data
        const formatted =
          Array.isArray(resultData) && resultData.length
            ? resultData
                .map((obj) =>
                  Object.entries(obj)
                    .map(([key, val]) => `${key}: ${val}`)
                    .join("\n")
                )
                .join("\n\n")
            : typeof resultData === "string"
            ? resultData
            : "No data found.";

        newMessages.push({
          type: "incoming",
          isSqlQuery: true,
          heading: " Data + Query from your text",
          text: `Data: ${formatted}\n\nQuery: ${sql}`,
        });
        setLastBotText(resultData);
      }

      setMessages((prev) => [...prev, ...newMessages]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { type: "incoming", text: "\u274c Error reaching the server." },
      ]);
    }
    setLoading(false);
  };

  const handleMicClick = () => {
    if (!("webkitSpeechRecognition" in window)) {
      alert("Speech recognition not supported in your browser.");
      return;
    }
    const recognition = new window.webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.start();
    setIsListening(true);
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      sendMessage(transcript);
    };
    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);
  };

  const parseChartData = () => {
    if (!Array.isArray(lastBotText) || lastBotText.length === 0) return null;

    const sample = lastBotText[0];
    console.log("Sample chart row:", sample);

    const labelKey =
      Object.keys(sample).find((k) =>
        ["month", "branch_name", "category", "date", "name", "label"].includes(
          k
        )
      ) || Object.keys(sample)[0]; // fallback

    const valueKeys = Object.keys(sample).filter(
      (key) => key !== labelKey && typeof sample[key] === "number"
    );

    if (!labelKey || valueKeys.length === 0) {
      console.log("Invalid labelKey or valueKeys", { labelKey, valueKeys });
      return null;
    }

    const labels = lastBotText.map((item) => item[labelKey]);
    const datasets = valueKeys.map((valKey) => ({
      label: valKey.replace(/_/g, " "),
      data: lastBotText.map((item) => item[valKey]),
    }));

    console.log("Chart labels:", labels);
    console.log("Chart datasets:", datasets);

    return { labels, datasets };
  };

  console.log("Chart Data:", parseChartData());

  function parseTableData() {
    if (Array.isArray(lastBotText) && lastBotText.length > 0) {
      return lastBotText.map((item) => {
        const row = {};
        for (const key in item) {
          row[key] = item[key];
        }
        return row;
      });
    }
    return [];
  }

  return (
    <div className="min-h-screen bg-[#cceafb] text-white font-sans overflow-hidden py-5 p-6 md:p-10">
      <div className="flex justify-between items-center mb-6 md:mb-8">
        <img
          src={logo}
          onClick={() => navigate("/")}
          alt="Logo"
          className="h-10 cursor-pointer"
        />
        <p className="text-l  text-black bg-gradient-to-r   uppercase">
          Developed by Chandan
        </p>
      </div>

      <header className="max-w-4xl mx-auto p-4">
        {!firstUserMessageSent && (
          <div>
            <h1 className="text-5xl flex justify-center font-bold bg-gradient-to-r from-blue-500 to-black bg-clip-text text-transparent text-center">
              Hello, Team
              <span>
                <img src={logo} alt="Logo" className="h-16 ml-1 p-1" />
              </span>
            </h1>

            <p className="text-3xl flex font-bold bg-gradient-to-r from-blue-800 to-black bg-clip-text text-transparent text-center">
              From question to query — turn natural language into real SQL
              insights
            </p>
          </div>
        )}

        <button
          className="text-black font-medium mt-4"
          onClick={() => setShowSuggestions(!showSuggestions)}
        >
          {showSuggestions ? "▲ Hide suggestions" : "▼ Show suggestions"}
        </button>

        {showSuggestions && (
          <ul className="flex gap-5 mt-5 overflow-x-auto scrollbar-hide">
            {suggestions.map(({ text, icon }, idx) => (
              <li
                key={idx}
                onClick={() => sendMessage(text)}
                className="min-w-[222px] bg-[#1e2237] hover:bg-[#2a2e4d] cursor-pointer p-5 rounded-xl flex flex-col justify-between"
              >
                <h4 className="text-white text-sm leading-snug">{text}</h4>
                <div className="w-7 h-7 mt-5 rounded-full flex items-center justify-center bg-black text-white">
                  {icon}
                </div>
              </li>
            ))}
          </ul>
        )}

        <div className="flex items-center justify-center mt-4 text-black ">
          <button
            onClick={() => setGetSQLQuery(!getSQLQuery)}
            className={`relative w-[360px] border border-gray-500 h-14 rounded-full px-1 transition-colors duration-300 overflow-hidden ${
              getSQLQuery ? "bg-red-100" : "bg-blue-200"
            }`}
          >
            <motion.div
              layout
              transition={{
                type: "spring",
                duration: 0.4,
                bounce: 0.3,
              }}
              animate={{
                x: getSQLQuery ? 180 : 0,
              }}
              className={`absolute top-1 left-1 w-[170px] h-12 rounded-full text-white text-sm font-bold flex items-center justify-center text-center px-2 transition-colors mx- ${
                getSQLQuery ? "bg-red-500" : "bg-blue-500"
              }`}
            >
              {getSQLQuery ? "Get SQL Query  " : "Get Data With Query "}
            </motion.div>

            {/* Optional static background text (dimmed for clarity) */}
            <div className="flex w-full justify-between px-5 text-xs font-medium z-10 text-gray-600 h-full items-center whitespace-nowrap mx-2">
              <span>Get Data Along With Query</span>
              <span>Get SQL Query from Prompt </span>
            </div>
          </button>
        </div>
      </header>

      <div
        ref={chatRef}
        className="chat-list max-w-4xl mx-auto px-4 py-8 overflow-y-auto scrollbar-hide"
        style={{ maxHeight: "calc(100vh - 260px)", paddingBottom: "10rem" }}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`my-4 flex ${
              msg.type === "outgoing" ? "justify-end" : "justify-start"
            }`}
          >
            <div className="flex gap-3 items-start max-w-[80%]">
              {msg.type === "incoming" && (
                <div className="w-10 h-10 rounded-full flex items-center justify-center overflow-hidden">
                  <img
                    src={chase}
                    alt="Chase"
                    className="w-8 h-8 object-contain"
                  />
                </div>
              )}

              <div
                className={`rounded-xl px-4 py-2 text-white text-base md:text-lg ${
                  msg.type === "outgoing"
                    ? "bg-blue-600 rounded-br-none"
                    : "bg-gray-700 rounded-bl-none"
                }`}
              >
                {/* SQL query response (formatted with header) */}
                {msg.isSqlQuery ? (
                  <div>
                    <div className="text-blue-400 font-semibold mb-2">
                      {msg.heading}
                    </div>
                    <div className="text-sm font-mono whitespace-pre-wrap">
                      {msg.text}
                    </div>
                  </div>
                ) : msg.isCombinedQuery ? (
                  <div>
                    <div className="text-red-400 font-semibold mb-2">
                      {msg.heading}
                    </div>
                    <div className="text-sm whitespace-pre-wrap mb-2">
                      <strong className="text-white">Data:</strong>{" "}
                      <span className="text-gray-200">{msg.dataText}</span>
                    </div>
                    <div className="text-sm font-mono text-gray-300 whitespace-pre-wrap">
                      <strong className="text-white">Query:</strong>{" "}
                      {msg.sqlText}
                    </div>
                  </div>
                ) : (
                  msg.text
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 items-start mt-4">
            <div className="w-10 h-10 rounded-full animate-spin text-white flex items-center justify-center">
              <img src={chase} alt="Chase" className="w-8 h-8 object-contain" />
            </div>
            <div className="space-y-2 w-full">
              <div className="h-3 w-full rounded bg-gradient-to-r from-blue-600 via-gray-800 to-blue-500 animate-pulse"></div>
              <div className="h-3 w-3/4 rounded bg-gradient-to-r from-blue-600 via-gray-800 to-blue-500 animate-pulse"></div>
            </div>
          </div>
        )}

        {toolType === "bar" &&
          Array.isArray(lastBotText) &&
          lastBotText.length > 0 && (
            <div className="mt-6">
              <ChartRenderer type="bar" data={parseChartData()} />
            </div>
          )}

        {toolType === "line" &&
          Array.isArray(lastBotText) &&
          lastBotText.length > 0 && (
            <div className="mt-6">
              <ChartRenderer type="line" data={parseChartData()} />
            </div>
          )}

        {toolType === "table" &&
          Array.isArray(lastBotText) &&
          lastBotText.length > 0 && <TableRenderer data={parseTableData()} />}
      </div>

      <div className="fixed bottom-0 w-full bg-[#cceafb] p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage(input);
          }}
          className="max-w-4xl mx-auto flex items-center gap-3"
        >
          <div className="relative">
            <button
              type="button"
              onClick={() => setToolOpen(!toolOpen)}
              className="w-12 h-12 bg-[#1f2235] hover:bg-[#2a2e4d] rounded-full flex items-center justify-center text-white"
              title="Tools"
            >
              <TuneIcon />
            </button>
            {toolOpen && (
              <div className="absolute bottom-16 left-0 w-48 bg-[#1e2237] shadow-lg rounded-xl text-white p-2 z-50">
                {["Text", "Table", "Bar"].map((type) => (
                  <div
                    key={type}
                    onClick={() => {
                      setToolType(
                        type.toLowerCase().includes("line")
                          ? "line"
                          : type.toLowerCase().includes("bar")
                          ? "bar"
                          : type.toLowerCase().includes("table")
                          ? "table"
                          : "text"
                      );
                      setToolOpen(false);
                    }}
                    className={`flex items-center gap-2 p-2 rounded cursor-pointer hover:bg-[#2a2e4d] ${
                      toolType === type ? "bg-[#2a2e4d] font-semibold" : ""
                    }`}
                  >
                    {type === "Text" && <TextFieldsIcon />}
                    {type === "Bar" && <BarChartIcon />}
                    {type === "Line Graph" && <InsightsIcon />}
                    {type === "Table" && <TableChartIcon />}
                    <span className="capitalize">{type}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything..."
            className="flex-1 h-14 rounded-full px-6 bg-[#1f2235] text-white placeholder-gray-400 focus:outline-none text-base md:text-lg"
            required
          />

          <button
            type="submit"
            className="w-12 h-12 bg-blue-600 hover:bg-blue-700 rounded-full flex items-center justify-center text-white"
          >
            <SendIcon />
          </button>

          <button
            type="button"
            onClick={handleMicClick}
            className={`bg-[#1f2235] hover:bg-[#2a2e4d] w-12 h-12 rounded-full flex items-center justify-center text-white transition ${
              isListening ? "animate-pulse bg-red-400" : ""
            }`}
            title="Speak"
          >
            <MicIcon />
          </button>
        </form>
      </div>
    </div>
  );
}
