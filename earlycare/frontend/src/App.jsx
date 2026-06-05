import React, { useState, useEffect, useMemo } from "react";
import axios from "axios";

function App() {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [modelType, setModelType] = useState("diabetes");

  // Define fields based on your specific CSV structures
  const fieldConfig = useMemo(
    () => ({
      diabetes: [
        "gender",
        "age",
        "hypertension",
        "heart_disease",
        "smoking_history",
        "bmi",
        "HbA1c_level",
        "blood_glucose_level",
      ],
      heart: [
        "age",
        "sex",
        "cp",
        "trestbps",
        "chol",
        "fbs",
        "restecg",
        "thalach",
        "exang",
        "oldpeak",
        "slope",
        "ca",
        "thal",
      ],
      liver: [
        "Age",
        "Gender",
        "Total_Bilirubin",
        "Direct_Bilirubin",
        "Alkaline_Phosphotase",
        "Alamine_Aminotransferase",
        "Aspartate_Aminotransferase",
        "Total_Protiens",
        "Albumin",
        "Albumin_and_Globulin_Ratio",
      ],
    }),
    []
  );

  const [reportData, setReportData] = useState({});

  // Initialize reportData when modelType changes
  useEffect(() => {
    const initialData = {};
    fieldConfig[modelType].forEach((field) => (initialData[field] = ""));
    setReportData(initialData);
  }, [modelType, fieldConfig]);

  const [symptoms, setSymptoms] = useState({
    fever: 0,
    fatigue: 0,
    cough: 0,
    shortnessOfBreath: 0,
    dizziness: 0,
    nausea: 0,
    excessiveThirst: 0,
    blurredVision: 0,
  });

  const [history, setHistory] = useState({
    asthma: 0,
    hypertension: 0,
    diabetesInFamily: 0,
    heartDisease: 0,
    liverCondition: 0,
    smokingHistory: 0,
  });

  const handleInputChange = (e) => {
    setReportData({ ...reportData, [e.target.name]: e.target.value });
  };

  const toggleCheck = (type, name) => {
    const setter = type === "symptom" ? setSymptoms : setHistory;
    setter((prev) => ({ ...prev, [name]: prev[name] === 0 ? 1 : 0 }));
  };

  const handlePredict = async () => {
    setLoading(true);
    try {
      let symp = Object.values(symptoms);
      // For diabetes model, remove the last symptom (blurredVision) to match 21-feature model
      if (modelType === "diabetes") {
        symp = symp.slice(0, -1);
      }

      const data = {
        type: modelType,
        features: Object.values(reportData).map((val) => {
          // Basic handling for text inputs like 'Male'/'Female' if entered manually
          if (val.toLowerCase() === "male" || val.toLowerCase() === "m")
            return 1;
          if (val.toLowerCase() === "female" || val.toLowerCase() === "f")
            return 0;
          return parseFloat(val) || 0;
        }),
        symptoms: symp,
        history: Object.values(history),
      };

      const res = await axios.post("http://127.0.0.1:5001/predict", data);
      setPrediction(res.data.prediction);
    } catch (error) {
      console.error("Prediction failed:", error);
      alert("Prediction failed. Ensure Flask server is running.");
    } finally {
      setLoading(false);
    }
  };

  const formatName = (name) =>
    name
      .replace(/_/g, " ")
      .replace(/([A-Z])/g, " $1")
      .replace(/^./, (str) => str.toUpperCase());

  return (
    <div
      style={{
        padding: "30px",
        maxWidth: "1000px",
        margin: "auto",
        fontFamily: "Segoe UI",
      }}
    >
      <h1 style={{ textAlign: "center", color: "#2c3e50" }}>
        EarlyCare: Professional Health Analysis
      </h1>

      <div
        style={{
          marginBottom: "20px",
          padding: "15px",
          background: "#f1f2f6",
          borderRadius: "10px",
          textAlign: "center",
        }}
      >
        <label>
          <strong>Select Analysis Type: </strong>
        </label>
        <select
          value={modelType}
          onChange={(e) => setModelType(e.target.value)}
          style={{ padding: "8px", borderRadius: "5px" }}
        >
          <option value="diabetes">Diabetes (8 Features)</option>
          <option value="heart">Heart Disease (13 Features)</option>
          <option value="liver">Liver Condition (10 Features)</option>
        </select>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.2fr 1fr",
          gap: "20px",
        }}
      >
        <div style={cardStyle}>
          <h3
            style={{ borderBottom: "2px solid #3498db", paddingBottom: "10px" }}
          >
            1. Lab Report Values
          </h3>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "15px",
            }}
          >
            {fieldConfig[modelType].map((field) => {
              const isGenderField =
                field.toLowerCase() === "gender" ||
                field.toLowerCase() === "sex";

              return (
                <div key={field}>
                  <label style={{ fontSize: "13px", fontWeight: "bold" }}>
                    {formatName(field)}
                  </label>
                  {isGenderField ? (
                    <select
                      name={field}
                      value={reportData[field] || ""}
                      onChange={handleInputChange}
                      style={{
                        width: "100%",
                        padding: "10px",
                        marginTop: "5px",
                        borderRadius: "6px",
                        border: "1px solid #ced4da",
                        boxSizing: "border-box",
                        fontSize: "14px",
                      }}
                    >
                      <option value="">Select Gender</option>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                    </select>
                  ) : (
                    <input
                      type="text"
                      name={field}
                      placeholder="Value"
                      value={reportData[field] || ""}
                      onChange={handleInputChange}
                      style={inputStyle}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div>
          <div style={{ ...cardStyle, marginBottom: "20px" }}>
            <h3>2. Symptoms</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr" }}>
              {Object.keys(symptoms).map((s) => (
                <label key={s} style={labelStyle}>
                  <input
                    type="checkbox"
                    onChange={() => toggleCheck("symptom", s)}
                  />{" "}
                  {formatName(s)}
                </label>
              ))}
            </div>
          </div>
          <div style={cardStyle}>
            <h3>3. Medical History</h3>
            {Object.keys(history).map((h) => (
              <label key={h} style={labelStyle}>
                <input
                  type="checkbox"
                  onChange={() => toggleCheck("history", h)}
                />{" "}
                {formatName(h)}
              </label>
            ))}
          </div>
        </div>
      </div>

      <button
        onClick={handlePredict}
        disabled={loading}
        style={{
          ...btnStyle,
          width: "100%",
          marginTop: "30px",
          background: "#27ae60",
        }}
      >
        {loading ? "Calculating Risk..." : "Generate Diagnosis Report"}
      </button>

      {prediction !== null && (
        <div
          style={{
            marginTop: "30px",
            padding: "25px",
            textAlign: "center",
            borderRadius: "10px",
            color: "white",
            background: prediction === 1 ? "#e74c3c" : "#2ecc71",
            boxShadow: "0 4px 15px rgba(0,0,0,0.2)",
          }}
        >
          <h2 style={{ margin: 0 }}>
            Result:{" "}
            {prediction === 1
              ? "⚠️ High Risk Detected"
              : "✅ Low Risk / Normal"}
          </h2>
          <p>
            Based on {modelType.charAt(0).toUpperCase() + modelType.slice(1)}{" "}
            model and provided symptoms.
          </p>
        </div>
      )}
    </div>
  );
}

const cardStyle = {
  background: "#fff",
  padding: "20px",
  borderRadius: "12px",
  boxShadow: "0 4px 6px rgba(0,0,0,0.05)",
  border: "1px solid #dfe4ea",
};
const inputStyle = {
  width: "100%",
  padding: "10px",
  marginTop: "5px",
  borderRadius: "6px",
  border: "1px solid #ced4da",
  boxSizing: "border-box",
};
const labelStyle = {
  display: "block",
  marginBottom: "10px",
  cursor: "pointer",
  fontSize: "14px",
};
const btnStyle = {
  padding: "15px",
  border: "none",
  borderRadius: "8px",
  color: "white",
  fontWeight: "bold",
  fontSize: "18px",
  cursor: "pointer",
  transition: "0.3s",
};

export default App;
