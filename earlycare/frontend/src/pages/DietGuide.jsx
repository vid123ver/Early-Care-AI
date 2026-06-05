import React, { useState } from "react";
import { getDietRecommendation } from "../api/dietApi";

const CONDITIONS = [
  "Auto (use my reports & symptoms)",
  "Diabetes",
  "High Cholesterol",
  "Liver Disease / Fatty Liver",
];

const DietGuide = () => {
  const [condition, setCondition] = useState(
    "Auto (use my reports & symptoms)",
  );
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const runDiet = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await getDietRecommendation({
        condition,
        // Backend will pull labs/history from all your reports using your login.
        labs: {},
        history: {},
        // Treat notes as symptoms/concerns.
        symptoms_text: notes,
      });
      setResult(res.data);
    } catch (e) {
      console.error("Diet recommendation failed:", e);
      setError(e.response?.data?.error || "Failed to load diet guidance");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="symptom-page">
      <div className="symptom-container">
        <h1 className="symptom-title">Diet Recommendations</h1>
        <div className="symptom-subtitle">
          Personalized, condition-based food guidance – what to eat and what to
          limit.
        </div>

        <div className="symptom-card" style={{ marginBottom: "1.5rem" }}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem" }}>
            <div style={{ minWidth: 220 }}>
              <div className="symptom-label">Condition / focus area</div>
              <select
                value={condition}
                onChange={(e) => setCondition(e.target.value)}
                className="auth-input"
              >
                {CONDITIONS.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div style={{ flex: 1, minWidth: 240 }}>
              <div className="symptom-label">
                Your symptoms / concerns (optional)
              </div>
              <textarea
                className="symptom-textarea"
                rows={3}
                placeholder="Example: high HbA1c in reports, tiredness, chest heaviness after walking, fatty liver on scan"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
          </div>

          <div className="symptom-actions" style={{ marginTop: "1.2rem" }}>
            <button
              type="button"
              onClick={runDiet}
              disabled={loading}
              className="btn-primary"
            >
              {loading ? "Generating plan..." : "Show diet plan"}
            </button>
            <button
              type="button"
              onClick={() => {
                setResult(null);
                setError("");
              }}
              className="btn-secondary"
            >
              Clear
            </button>
          </div>

          {error && (
            <div className="auth-alert-error" style={{ marginTop: 12 }}>
              {error}
            </div>
          )}
        </div>

        {result && (
          <div className="symptom-card" style={{ marginBottom: "1.5rem" }}>
            <div className="symptom-section-title">Overview</div>
            <div style={{ marginBottom: "0.75rem", color: "#1b6fbb" }}>
              {result.profile}
            </div>
            <div style={{ fontSize: "0.9rem", color: "#6a8ca4" }}>
              {result.disclaimer}
            </div>
          </div>
        )}

        {result && (
          <div
            className="symptom-card"
            style={{
              display: "grid",
              gap: "1.5rem",
              gridTemplateColumns: "1fr 1fr",
            }}
          >
            <div>
              <div className="symptom-section-title">Eat more of</div>
              <ul
                className="list-disc"
                style={{ paddingLeft: "1.25rem", color: "#234567" }}
              >
                {(result.eat_more || []).map((item, idx) => (
                  <li key={idx} style={{ marginBottom: 4 }}>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="symptom-section-title">Limit / avoid</div>
              <ul
                className="list-disc"
                style={{ paddingLeft: "1.25rem", color: "#b42323" }}
              >
                {(result.eat_less_or_avoid || []).map((item, idx) => (
                  <li key={idx} style={{ marginBottom: 4 }}>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {result && result.sample_chart && (
          <div className="symptom-card" style={{ marginTop: "1.5rem" }}>
            <div className="symptom-section-title">Example day plan</div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                gap: "1rem",
                marginTop: "0.75rem",
              }}
            >
              {Object.entries(result.sample_chart).map(([meal, options]) => (
                <div
                  key={meal}
                  style={{
                    borderRadius: 12,
                    border: "1px solid #e0eafc",
                    padding: "0.9rem 1rem",
                    background: "#f8fbff",
                  }}
                >
                  <div
                    style={{
                      fontWeight: 700,
                      color: "#1b6fbb",
                      textTransform: "capitalize",
                      marginBottom: 6,
                    }}
                  >
                    {meal}
                  </div>
                  <ul
                    className="list-disc"
                    style={{ paddingLeft: "1.25rem", fontSize: "0.9rem" }}
                  >
                    {options.map((opt, idx) => (
                      <li key={idx} style={{ marginBottom: 3 }}>
                        {opt}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
            {Array.isArray(result.notes) && result.notes.length > 0 && (
              <div style={{ marginTop: "1rem" }}>
                <div className="symptom-section-title">Additional notes</div>
                <ul
                  className="list-disc"
                  style={{ paddingLeft: "1.25rem", fontSize: "0.9rem" }}
                >
                  {result.notes.map((n, idx) => (
                    <li key={idx} style={{ marginBottom: 3 }}>
                      {n}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DietGuide;
