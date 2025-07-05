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
  const [getSQLQuery, setGetSQLQuery] = useState(false);
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
      const res = await fetch(
        // `https://text-to-sql-vw6i.onrender.com/${endpoint}`,
        ` http://localhost:8000/${endpoint}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: msg }),
        }
      );

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
      <div className="flex flex-col sm:flex-row justify-between items-center text-center gap-2 mb-6 md:mb-8">
        <img
          src={logo}
          onClick={() => navigate("/")}
          alt="Logo"
          className="h-10 cursor-pointer"
        />
        <a
          href="https://www.linkedin.com/in/chandan-allimilli/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-l text-black bg-gradient-to-r uppercase hover:underline"
        >
          Developed by Chandan
        </a>
      </div>

      <header className="max-w-4xl mx-auto p-4">
        {!firstUserMessageSent && (
          <div>
            <div className="flex items-center justify-center gap-2 flex-wrap md:flex-nowrap">
              <h1 className="text-3xl md:text-5xl font-bold bg-gradient-to-r from-blue-500 to-black bg-clip-text text-transparent text-center">
                Hello, Team
              </h1>
              <img src={logo} alt="Logo" className="h-16 md:h-20 pt-4" />
            </div>

            <p className="text-xl md:text-3xl flex font-bold bg-gradient-to-r from-blue-800 to-black bg-clip-text text-transparent text-center">
              From question to query — turn natural language into real SQL
              insights
            </p>
          </div>
        )}

        <button
          className="bg-gradient-to-r from-blue-900 to-black bg-clip-text text-transparent font-medium mt-4"
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
                className="min-w-[222px] bg-gradient-to-r from-gray-900 to-gray-700 hover:bg-[#2a2e4d] cursor-pointer p-5 rounded-xl flex flex-col justify-between"
              >
                <h4 className="text-white text-sm leading-snug">{text}</h4>
                <div className="w-7 h-7 mt-5 rounded-full flex items-center justify-center bg-black text-white">
                  {icon}
                </div>
              </li>
            ))}
          </ul>
        )}

        <div className="flex items-center justify-center mt-4 text-black px-3">
          <button
            onClick={() => setGetSQLQuery(!getSQLQuery)}
            className={`relative w-full max-w-xs sm:max-w-md lg:w-[360px] border border-gray-500 h-14 rounded-full transition-colors duration-300 overflow-hidden ${
              getSQLQuery
                ? "bg-gradient-to-r from-red-200 to-red-400"
                : "bg-gradient-to-r from-blue-200 to-blue-400"
            }`}
          >
            <motion.div
              layout
              transition={{
                type: "spring",
                duration: 0.3,
                bounce: 0.6,
              }}
              animate={{
                left: getSQLQuery ? "50%" : "0%",
              }}
              className={`absolute top-1 h-12 w-1/2 px-2 rounded-full text-white text-sm font-bold flex items-center justify-center transition-all duration-75 ${
                getSQLQuery
                  ? "bg-gradient-to-r from-red-500 to-red-800"
                  : "bg-gradient-to-r from-blue-400 to-blue-800"
              }`}
            >
              {getSQLQuery ? "Get SQL Query" : "Get Data"}
            </motion.div>

            <div className="flex w-full justify-between px-8 sm:px-5 text-xs font-medium z-10 text-gray-600 h-full items-center whitespace-nowrap">
              <span className="truncate">Get Data Along With Query</span>
              <span className="truncate">Get SQL Query from Prompt</span>
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
                    ? "bg-gradient-to-r from-blue-500 to-blue-800 rounded-br-none"
                    : "bg-gradient-to-r from-gray-900 to-gray-700 rounded-bl-none"
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

      <div className="fixed bottom-0 w-full bg-[#cceafb] p-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage(input);
          }}
          className="w-full max-w-4xl px-2 sm:px-4 md:px-0 mx-auto flex items-center gap-2"
        >
          {/* Tools Button */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setToolOpen(!toolOpen)}
              className="w-9 h-9 sm:w-10 sm:h-10 bg-gradient-to-r from-blue-500 to-blue-800  hover:bg-[#2a2e4d] rounded-full flex items-center justify-center text-white"
              title="Tools"
            >
              <TuneIcon className="text-xs sm:text-sm" />
            </button>

            {toolOpen && (
              <div className="absolute bottom-12 left-0 w-40 sm:w-48 bg-[#1e2237] shadow-lg rounded-xl text-white p-2 z-50">
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
                    className={`flex items-center gap-2 p-2 rounded bg-gradient-to-r from-gray-800 to-gray-900 cursor-pointer  ${
                      toolType === type
                        ? "bg-gradient-to-r from-blue-500 to-blue-800  font-semibold"
                        : ""
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

          {/* Input Field */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything..."
            className="flex-1 h-11 sm:h-12 rounded-full px-4  bg-gradient-to-r from-gray-900 to-gray-700 text-white placeholder-gray-400 focus:outline-none text-sm"
            required
          />

          {/* Send Button */}
          <button
            type="submit"
            className="w-9 h-9 sm:w-10 ml-[10px] sm:h-10 bg-gradient-to-r from-blue-500 to-blue-800  hover:bg-blue-700 rounded-full flex items-center justify-center text-white"
          >
            <SendIcon className="text-xs sm:text-sm" />
          </button>

          {/* Mic Button */}
          <button
            type="button"
            onClick={handleMicClick}
            className={`w-9 h-9 sm:w-10 sm:h-10 bg-gradient-to-r from-blue-500 to-blue-900 mr-8 rounded-full flex items-center justify-center text-white transition ${
              isListening
                ? "animate-pulse bg-gradient-to-r from-red-500 to-red-900"
                : ""
            }`}
            title="Speak"
          >
            <MicIcon className="text-xs sm:text-sm" />
          </button>
        </form>
      </div>
    </div>
  );
}
