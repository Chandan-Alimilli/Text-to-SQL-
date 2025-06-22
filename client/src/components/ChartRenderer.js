import React from "react";
import { Bar, Pie, Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  LineElement,
  PointElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  LineElement,
  PointElement,
  Tooltip,
  Legend
);

export default function ChartRenderer({ type, data }) {
  if (!data || !data.labels || !data.datasets) {
    return null; // 🛡️ Prevent rendering if data is incomplete
  }

  const options = {
    responsive: true,
    plugins: {
      legend: { position: "bottom" },
      tooltip: { mode: "index", intersect: false },
    },
  };

  if (type === "bar") return <Bar data={data} options={options} />;
  if (type === "pie") return <Pie data={data} options={options} />;
  if (type === "line") return <Line data={data} options={options} />;

  return null;
}
