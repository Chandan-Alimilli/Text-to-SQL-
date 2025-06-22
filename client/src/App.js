import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Chatbox from "./components/Chatbot";

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Chatbox />} />
      </Routes>
    </Router>
  );
};

export default App;
