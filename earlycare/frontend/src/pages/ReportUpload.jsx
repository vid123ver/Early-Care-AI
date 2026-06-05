import React, { useState } from "react";
import { uploadReport } from "../api/reportApi";

const ReportUpload = () => {
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [extractedText, setExtractedText] = useState("");
  const [metrics, setMetrics] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [risk, setRisk] = useState(null);
  const [explanation, setExplanation] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setProgress(0);
    setExtractedText("");
    setMetrics(null);
    setPrediction(null);
    setRisk(null);
    setExplanation("");
    setError("");
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await uploadReport(formData, (event) => {
        setProgress(Math.round((event.loaded * 100) / event.total));
      });
      setExtractedText(res.data.extracted_text || "");
      setMetrics(res.data.metrics || null);
      setPrediction(res.data.prediction || null);
      setRisk(res.data.risk || null);
      setExplanation(res.data.explanation || "");
    } catch (err) {
      setError(err.response?.data?.error || "Upload failed");
    }
    setLoading(false);
  };

  return (
    <div className="report-upload-container">
      <h2>Upload Medical Report (PDF)</h2>
      <input type="file" accept="application/pdf" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={!file || loading}>
        {loading ? "Uploading..." : "Upload"}
      </button>
      {progress > 0 && <div>Progress: {progress}%</div>}
      {error && <div style={{ color: "red" }}>{error}</div>}
      {extractedText && (
        <div>
          <h3>Extracted Text</h3>
          <pre
            style={{
              maxHeight: 200,
              overflow: "auto",
              background: "#f4f4f4",
              padding: 10,
            }}
          >
            {extractedText}
          </pre>
        </div>
      )}
      {metrics && (
        <div>
          <h3>Extracted Values</h3>
          <pre>{JSON.stringify(metrics, null, 2)}</pre>
        </div>
      )}
      {prediction && (
        <div>
          <h3>Disease Prediction</h3>
          <pre>{JSON.stringify(prediction, null, 2)}</pre>
        </div>
      )}
      {risk && (
        <div>
          <h3>Risk Score</h3>
          <pre>{JSON.stringify(risk, null, 2)}</pre>
        </div>
      )}
      {explanation && (
        <div>
          <h3>Medical Explanation</h3>
          <pre>{explanation}</pre>
        </div>
      )}
    </div>
  );
};

export default ReportUpload;
