import React, { useEffect, useState } from "react";
import { getDashboardOverview } from "../api/dashboardApi";
import HealthTrendsChart from "../components/HealthTrendsChart";
import { getHealthTrends } from "../api/dashboardApi";
import { getAlerts } from "../api/dashboardApi";
import { getLifestyle } from "../api/dashboardApi";
import { getReports } from "../api/reportApi";

const Dashboard = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [trends, setTrends] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [lifestyle, setLifestyle] = useState(null);
  const [emergencyMsg, setEmergencyMsg] = useState("");
  const [reports, setReports] = useState([]);
  const [selectedReportId, setSelectedReportId] = useState("");
  const [compareWithHistory, setCompareWithHistory] = useState(true);
  const [darkMode, setDarkMode] = useState(false);

  // Initialise theme from localStorage
  useEffect(() => {
    const stored = localStorage.getItem("earlycare-theme");
    const initialDark = stored === "dark";
    setDarkMode(initialDark);
    if (initialDark) {
      document.body.classList.add("dark-mode");
    } else {
      document.body.classList.remove("dark-mode");
    }
  }, []);

  // Keep body class and storage in sync when user toggles theme
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add("dark-mode");
      localStorage.setItem("earlycare-theme", "dark");
    } else {
      document.body.classList.remove("dark-mode");
      localStorage.setItem("earlycare-theme", "light");
    }
  }, [darkMode]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError("");
      try {
        const reportsRes = await getReports();
        const list = reportsRes.data.reports || [];
        setReports(list);
        const defaultId = list[0]?._id || "";
        setSelectedReportId((prev) => prev || defaultId);

        const [overviewRes, trendsRes, alertsRes, lifestyleRes] =
          await Promise.all([
            getDashboardOverview({
              report_id: selectedReportId || defaultId || undefined,
              compare: compareWithHistory,
            }),
            getHealthTrends(),
            getAlerts(),
            getLifestyle(),
          ]);
        setData(overviewRes.data);
        setTrends(trendsRes.data);
        setAlerts(alertsRes.data.alerts || []);
        setLifestyle(lifestyleRes.data || null);
        setEmergencyMsg(
          alertsRes.data.emergency
            ? alertsRes.data.emergency_message || ""
            : "",
        );
      } catch (error) {
        console.error("Dashboard load failed:", error);
        setError("Failed to load dashboard data");
      }
      setLoading(false);
    };
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedReportId, compareWithHistory]);

  if (loading)
    return <div className="text-center mt-20">Loading dashboard...</div>;
  if (error)
    return <div className="text-center text-red-600 mt-20">{error}</div>;
  if (!data) return null;

  return (
    <div
      className="medical-theme"
      style={{ minHeight: "100vh", padding: "2rem" }}
    >
      <h1
        style={{
          marginBottom: "2rem",
          fontWeight: 700,
          fontSize: "2.2rem",
          color: "#2b8be6",
          textAlign: "center",
        }}
      >
        Welcome to EarlyCare Dashboard
      </h1>

      <div
        style={{
          maxWidth: 900,
          margin: "0 auto 1.5rem auto",
          display: "flex",
          gap: "1rem",
          justifyContent: "center",
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", gap: ".5rem", alignItems: "center" }}>
          <span style={{ color: "#2b8be6", fontWeight: 600 }}>Report:</span>
          <select
            value={selectedReportId}
            onChange={(e) => setSelectedReportId(e.target.value)}
            style={{
              padding: ".5rem .75rem",
              borderRadius: 8,
              border: "1px solid #d0d7de",
              background: "white",
            }}
          >
            {reports.length === 0 ? (
              <option value="">No reports yet</option>
            ) : (
              reports.map((r) => (
                <option key={r._id} value={r._id}>
                  {(r.created_at
                    ? new Date(r.created_at).toLocaleString()
                    : "Unknown date") + (r.filename ? ` • ${r.filename}` : "")}
                </option>
              ))
            )}
          </select>
        </div>

        <label
          style={{
            display: "flex",
            gap: ".5rem",
            alignItems: "center",
            padding: ".5rem .75rem",
            borderRadius: 8,
            border: "1px solid #d0d7de",
            background: "white",
          }}
        >
          <input
            type="checkbox"
            checked={compareWithHistory}
            onChange={(e) => setCompareWithHistory(e.target.checked)}
          />
          <span style={{ fontWeight: 600, color: "#2b8be6" }}>
            Compare with previous history
          </span>
        </label>

        <button
          type="button"
          onClick={() => setDarkMode((prev) => !prev)}
          className="theme-toggle-btn"
        >
          {darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
        </button>
      </div>
      <div className="dashboard-cards">
        <div className="dashboard-card">
          <div className="dashboard-card-title">Health Score</div>
          <div className="dashboard-card-value">{data.health_score}</div>
          <div className="dashboard-card-desc">AI-evaluated overall health</div>
        </div>
        <div className="dashboard-card">
          <div className="dashboard-card-title">Latest Disease Prediction</div>
          <div className="dashboard-card-value">
            {data.latest_prediction || "N/A"}
          </div>
          <div className="dashboard-card-desc">Most recent model output</div>
        </div>
        <div className="dashboard-card">
          <div className="dashboard-card-title">Risk Level</div>
          <div className="dashboard-card-value">{data.risk_level || "N/A"}</div>
          <div className="dashboard-card-desc">Current patient risk</div>
        </div>
        <div className="dashboard-card">
          <div className="dashboard-card-title">Reports Uploaded</div>
          <div className="dashboard-card-value">{data.total_reports}</div>
          <div className="dashboard-card-desc">Total processed reports</div>
        </div>
      </div>

      {/* Health summary based on latest report and risk */}
      {data.health_summary_text && (
        <div style={{ maxWidth: 900, margin: "1rem auto 0 auto" }}>
          <div className="dashboard-card" style={{ width: "100%" }}>
            <div className="dashboard-card-title">Health summary</div>
            <div style={{ color: "#234567", fontSize: "0.95rem" }}>
              {data.health_summary_text}
            </div>
          </div>
        </div>
      )}

      {data.current_report?.metrics && (
        <div style={{ maxWidth: 900, margin: "1rem auto 0 auto" }}>
          <div className="dashboard-card" style={{ width: "100%" }}>
            <div className="dashboard-card-title">Current Report Metrics</div>
            <pre style={{ margin: 0 }}>
              {JSON.stringify(data.current_report.metrics, null, 2)}
            </pre>
            {compareWithHistory && data.comparison?.deltas && (
              <>
                <div className="dashboard-card-title" style={{ marginTop: 12 }}>
                  Change vs Previous Report
                </div>
                <pre style={{ margin: 0 }}>
                  {JSON.stringify(data.comparison.deltas, null, 2)}
                </pre>
              </>
            )}
          </div>
        </div>
      )}

      {/* Abnormal lab values from the latest report */}
      {Array.isArray(data.abnormal_markers) &&
        data.abnormal_markers.length > 0 && (
          <div style={{ maxWidth: 900, margin: "1rem auto 0 auto" }}>
            <div className="dashboard-card" style={{ width: "100%" }}>
              <div className="dashboard-card-title">Abnormal lab values</div>
              <ul
                style={{
                  margin: 0,
                  paddingLeft: "1.1rem",
                  fontSize: "0.9rem",
                  color: "#b42323",
                }}
              >
                {data.abnormal_markers.map((m, idx) => (
                  <li key={idx} style={{ marginBottom: 3 }}>
                    <strong style={{ textTransform: "capitalize" }}>
                      {m.marker}
                    </strong>{" "}
                    ({m.value}) – {m.message}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      <div className="chart-container">
        <h2
          style={{ color: "#2b8be6", fontWeight: 600, marginBottom: "1.5rem" }}
        >
          Health Trends
        </h2>
        {trends && (
          <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 260 }}>
              <HealthTrendsChart
                title="Glucose Trend"
                dataPoints={trends.glucose || []}
                label="Glucose (mg/dL)"
                color="#3b82f6"
                animate
              />
            </div>
            <div style={{ flex: 1, minWidth: 260 }}>
              <HealthTrendsChart
                title="Cholesterol Trend"
                dataPoints={trends.cholesterol || []}
                label="Cholesterol (mg/dL)"
                color="#f59e42"
                animate
              />
            </div>
            <div style={{ flex: 1, minWidth: 260 }}>
              <HealthTrendsChart
                title="Health Score Trend"
                dataPoints={trends.health_score || []}
                label="Health Score"
                color="#10b981"
                animate
              />
            </div>
          </div>
        )}
      </div>
      <div
        style={{
          display: "flex",
          gap: "2rem",
          marginTop: "2rem",
          flexWrap: "wrap",
        }}
      >
        <div className="dashboard-card" style={{ flex: 1, minWidth: 260 }}>
          <div className="dashboard-card-title">Recent Alerts</div>
          {data.top_health_concerns && data.top_health_concerns.length > 0 ? (
            <ul
              style={{
                color: "#e57373",
                margin: 0,
                padding: 0,
                listStyle: "disc inside",
              }}
            >
              {data.top_health_concerns.map((alert, i) => (
                <li key={i} style={{ marginBottom: 4 }}>
                  {alert}
                </li>
              ))}
            </ul>
          ) : (
            <div style={{ color: "#b0b0b0" }}>No recent alerts</div>
          )}
        </div>
        {alerts.length > 0 && (
          <div className="dashboard-card" style={{ flex: 1, minWidth: 260 }}>
            <div className="dashboard-card-title" style={{ color: "#e57373" }}>
              Critical Medical Alerts
            </div>
            <ul
              style={{
                color: "#e57373",
                margin: 0,
                padding: 0,
                listStyle: "disc inside",
              }}
            >
              {alerts.map((alert, i) => (
                <li key={i} style={{ marginBottom: 4 }}>
                  {alert}
                </li>
              ))}
            </ul>
            {emergencyMsg && (
              <div
                style={{
                  marginTop: "0.75rem",
                  fontWeight: 700,
                  color: "#b91c1c",
                  fontSize: "0.95rem",
                }}
              >
                {emergencyMsg}
              </div>
            )}
          </div>
        )}
        {lifestyle && (
          <div className="dashboard-card" style={{ flex: 1, minWidth: 260 }}>
            <div className="dashboard-card-title">
              Lifestyle &amp; prevention
            </div>
            {(lifestyle.sections || []).map((section, idx) => (
              <div key={idx} style={{ marginBottom: "0.75rem" }}>
                <div
                  style={{
                    fontWeight: 600,
                    marginBottom: 4,
                    color: "#2563eb",
                  }}
                >
                  {section.title}
                </div>
                <ul
                  style={{
                    margin: 0,
                    paddingLeft: "1.1rem",
                    fontSize: "0.9rem",
                    color: "#234567",
                  }}
                >
                  {(section.recommendations || []).map((r, i) => (
                    <li key={i} style={{ marginBottom: 2 }}>
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
            {lifestyle.disclaimer && (
              <div
                style={{
                  marginTop: "0.5rem",
                  fontSize: "0.75rem",
                  color: "#64748b",
                }}
              >
                {lifestyle.disclaimer}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
