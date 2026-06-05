import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getReport } from "../api/reportApi";
import apiClient from "../api/axiosInstance";

const ReportDetails = () => {
  const { reportId } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const res = await getReport(reportId);
        setReport(res.data.report);
      } catch (e) {
        console.error("Report details load failed:", e);
        setError(e.response?.data?.error || "Failed to load report");
      } finally {
        setLoading(false);
      }
    };
    if (reportId) load();
  }, [reportId]);

  if (loading)
    return <div className="text-center mt-20">Loading report...</div>;
  if (error)
    return <div className="text-center text-red-600 mt-20">{error}</div>;
  if (!report) return <div className="text-center mt-20">Report not found</div>;

  const handleDownloadPdf = async () => {
    if (!reportId) return;
    try {
      setDownloading(true);
      const res = await apiClient.get(`/report_pdf/${reportId}/download`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(
        new Blob([res.data], { type: "application/pdf" }),
      );
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `earlycare_report_${reportId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error("PDF download failed:", e);
      alert("Failed to download PDF report");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-10 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="mb-4">
          <Link
            to="/history"
            className="text-blue-600 underline hover:text-blue-800"
          >
            ← Back to history
          </Link>
        </div>

        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-blue-700">Report Details</h1>
          <button
            type="button"
            onClick={handleDownloadPdf}
            className="btn-primary"
            disabled={downloading}
          >
            {downloading ? "Preparing PDF..." : "Download PDF"}
          </button>
        </div>

        <div className="bg-white rounded shadow p-6 space-y-4">
          <div>
            <div className="text-sm text-gray-500">Uploaded</div>
            <div className="font-medium">
              {report.created_at
                ? new Date(report.created_at).toLocaleString()
                : "N/A"}
            </div>
          </div>

          <div>
            <div className="text-sm text-gray-500">Filename</div>
            <div className="font-medium">{report.filename || "N/A"}</div>
          </div>

          <div>
            <div className="text-sm text-gray-500 mb-1">Metrics</div>
            <pre className="bg-gray-50 p-3 rounded overflow-auto">
              {JSON.stringify(report.metrics || {}, null, 2)}
            </pre>
          </div>

          <div>
            <div className="text-sm text-gray-500 mb-1">
              Extracted Text (preview)
            </div>
            <pre className="bg-gray-50 p-3 rounded overflow-auto max-h-80">
              {report.extracted_text_preview || ""}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportDetails;
