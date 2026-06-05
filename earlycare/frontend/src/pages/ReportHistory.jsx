import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getReports } from "../api/reportApi";
import apiClient from "../api/axiosInstance";

const ReportHistory = () => {
  const navigate = useNavigate();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    const fetchReports = async () => {
      setLoading(true);
      setError("");
      try {
        const res = await getReports();
        setReports(res.data.reports || []);
      } catch (error) {
        console.error("Report history load failed:", error);
        setError("Failed to load report history");
      }
      setLoading(false);
    };
    fetchReports();
  }, []);

  if (loading)
    return <div className="text-center mt-20">Loading reports...</div>;
  if (error)
    return <div className="text-center text-red-600 mt-20">{error}</div>;

  const handleDownload = async (id) => {
    if (!id) return;
    try {
      setDownloadingId(id);
      const res = await apiClient.get(`/report_pdf/${id}/download`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(
        new Blob([res.data], { type: "application/pdf" }),
      );
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `earlycare_report_${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error("PDF download failed:", e);
      alert("Failed to download report summary");
    } finally {
      setDownloadingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-10 px-4">
      <h1 className="text-2xl font-bold text-blue-700 mb-8 text-center">
        Report History
      </h1>
      <div className="max-w-3xl mx-auto bg-white rounded shadow p-6">
        {reports.length === 0 ? (
          <div className="text-gray-500 text-center">
            No reports uploaded yet.
          </div>
        ) : (
          <table className="w-full text-left border-collapse">
            <thead>
              <tr>
                <th className="py-2 px-4 border-b">Upload Date</th>
                <th className="py-2 px-4 border-b">Filename</th>
                <th className="py-2 px-4 border-b">Metrics</th>
                <th className="py-2 px-4 border-b">View</th>
                <th className="py-2 px-4 border-b">Summary</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((r) => (
                <tr key={r._id} className="hover:bg-gray-50">
                  <td className="py-2 px-4 border-b">
                    {r.created_at
                      ? new Date(r.created_at).toLocaleString()
                      : "N/A"}
                  </td>
                  <td className="py-2 px-4 border-b">{r.filename || "N/A"}</td>
                  <td className="py-2 px-4 border-b">
                    {r.metrics ? Object.keys(r.metrics).length : 0}
                  </td>
                  <td className="py-2 px-4 border-b">
                    <button
                      className="text-blue-600 underline hover:text-blue-800"
                      onClick={() => navigate(`/history/${r._id}`)}
                    >
                      View
                    </button>
                  </td>
                  <td className="py-2 px-4 border-b">
                    <button
                      className="text-blue-600 underline hover:text-blue-800"
                      onClick={() => handleDownload(r._id)}
                      disabled={downloadingId === r._id}
                    >
                      {downloadingId === r._id
                        ? "Preparing..."
                        : "Download summary"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default ReportHistory;
