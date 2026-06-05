import React from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
);

const HealthTrendsChart = ({ title, dataPoints, label, color }) => {
  const normalized = (dataPoints || []).map((d) => {
    if (d && typeof d === "object" && "x" in d && "y" in d) {
      return { date: d.x, value: d.y };
    }
    return d;
  });
  const data = {
    labels: normalized.map((d) => d.date),
    datasets: [
      {
        label,
        data: normalized.map((d) => d.value),
        borderColor: color,
        backgroundColor: color + "33",
        tension: 0.3,
        fill: true,
      },
    ],
  };
  const options = {
    responsive: true,
    plugins: {
      legend: { display: false },
      title: { display: true, text: title },
    },
    scales: {
      x: { title: { display: true, text: "Date" } },
      y: { title: { display: true, text: label } },
    },
  };
  return <Line data={data} options={options} />;
};

export default HealthTrendsChart;
