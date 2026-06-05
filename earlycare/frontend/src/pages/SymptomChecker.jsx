import React, { useMemo, useState } from "react";
import { checkSymptoms } from "../api/symptomApi";
import { getTreatmentSuggestions } from "../api/treatmentApi";

const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

const SymptomChecker = () => {
  const [symptomsText, setSymptomsText] = useState("");
  const [answers, setAnswers] = useState({});
  const [results, setResults] = useState([]);
  const [nextQuestion, setNextQuestion] = useState(null);
  const [redFlags, setRedFlags] = useState([]);
  const [selectedCondition, setSelectedCondition] = useState("");
  const [treatment, setTreatment] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [listening, setListening] = useState(false);

  const speechSupported = useMemo(() => Boolean(SpeechRecognition), []);

  const runCheck = async (override = {}) => {
    setLoading(true);
    setError("");
    try {
      const res = await checkSymptoms({
        symptoms_text: override.symptomsText ?? symptomsText,
        answers: override.answers ?? answers,
      });
      setResults(res.data.results || []);
      setNextQuestion(res.data.next_question || null);
      setRedFlags(res.data.red_flags || []);
      const top = (res.data.results || [])[0]?.condition || "";
      setSelectedCondition((prev) => prev || top);
    } catch (e) {
      console.error("Symptom check failed:", e);
      setError(e.response?.data?.error || "Symptom check failed");
    } finally {
      setLoading(false);
    }
  };

  const startVoice = () => {
    if (!speechSupported) return;
    const rec = new SpeechRecognition();
    rec.lang = "en-US";
    rec.interimResults = true;
    rec.continuous = false;
    setListening(true);

    rec.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((r) => r[0]?.transcript || "")
        .join(" ")
        .trim();
      if (transcript)
        setSymptomsText((prev) =>
          prev ? `${prev} ${transcript}` : transcript,
        );
    };
    rec.onerror = (evt) => {
      console.error("Speech recognition error:", evt);
      setListening(false);
    };
    rec.onend = () => setListening(false);
    rec.start();
  };

  const answerFollowUp = async (yes) => {
    if (!nextQuestion?.question) return;
    // Store the question as key; backend tokenizes it and treats True as present symptom.
    const updated = {
      ...answers,
      [nextQuestion.question.toLowerCase()]: Boolean(yes),
    };
    setAnswers(updated);
    await runCheck({ answers: updated });
  };

  const loadTreatment = async () => {
    if (!selectedCondition) return;
    setLoading(true);
    setError("");
    try {
      const res = await getTreatmentSuggestions({
        condition: selectedCondition,
        symptoms_text: symptomsText,
        red_flags: redFlags,
      });
      setTreatment(res.data);
    } catch (e) {
      console.error("Treatment suggestion failed:", e);
      setError(
        e.response?.data?.error || "Failed to load treatment suggestions",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="symptom-page">
      <div className="symptom-container">
        <h1 className="symptom-title">Symptom Checker</h1>
        <div className="symptom-subtitle">
          Enter symptoms (text or voice). You&apos;ll get probability-ranked
          suggestions and smart follow-up questions.
        </div>

        <div className="symptom-card space-y-4">
          <div>
            <label className="symptom-label">Symptoms</label>
            <textarea
              value={symptomsText}
              onChange={(e) => setSymptomsText(e.target.value)}
              rows={4}
              placeholder="Example: fever, cough, sore throat, fatigue"
              className="symptom-textarea"
            />
            <div className="symptom-actions">
              <button
                type="button"
                onClick={() => runCheck()}
                disabled={loading || !symptomsText.trim()}
                className="btn-primary"
              >
                {loading ? "Analyzing..." : "Analyze"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setSymptomsText("");
                  setAnswers({});
                  setResults([]);
                  setNextQuestion(null);
                  setRedFlags([]);
                  setSelectedCondition("");
                  setTreatment(null);
                  setError("");
                }}
                className="btn-secondary"
              >
                Clear
              </button>
              <button
                type="button"
                onClick={startVoice}
                disabled={!speechSupported || listening}
                className="btn-secondary"
              >
                {speechSupported
                  ? listening
                    ? "Listening..."
                    : "Voice Input"
                  : "Voice not supported"}
              </button>
            </div>
          </div>

          {error && <div className="auth-alert-error">{error}</div>}

          {redFlags.length > 0 && (
            <div className="border border-red-200 bg-red-50 rounded p-4">
              <div
                className="symptom-section-title"
                style={{ color: "#b42323" }}
              >
                Important – possible emergency
              </div>
              <ul className="list-disc pl-5" style={{ color: "#b42323" }}>
                {redFlags.map((m, idx) => (
                  <li key={idx}>{m}</li>
                ))}
              </ul>
              <div
                style={{
                  marginTop: "0.5rem",
                  fontSize: "0.85rem",
                  fontWeight: 600,
                  color: "#b91c1c",
                }}
              >
                Immediate doctor consultation required.
              </div>
            </div>
          )}

          {results.length > 0 && (
            <div>
              <div className="symptom-section-title">
                Possible conditions (probability)
              </div>
              <div className="space-y-2">
                {results.map((r) => (
                  <div key={r.condition} className="symptom-pill-card">
                    <div>
                      <div className="font-semibold">{r.condition}</div>
                      <div className="text-xs text-gray-500">
                        matched: {r.matched_symptoms} / {r.model_coverage}
                      </div>
                    </div>
                    <div className="symptom-pill-prob">
                      {Math.round((r.probability || 0) * 100)}%
                    </div>
                  </div>
                ))}
              </div>
              <div className="text-xs text-gray-500 mt-2">
                This is not a diagnosis. Use this as guidance and consult a
                clinician for medical decisions.
              </div>

              <div className="mt-4 border-t pt-4">
                <div className="symptom-section-title">
                  Medicine &amp; treatment suggestions (OTC + home care)
                </div>
                <div className="flex gap-2 items-center flex-wrap">
                  <select
                    value={selectedCondition}
                    onChange={(e) => setSelectedCondition(e.target.value)}
                    className="border rounded p-2"
                  >
                    {(results || []).map((r) => (
                      <option key={r.condition} value={r.condition}>
                        {r.condition}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={loadTreatment}
                    disabled={loading || !selectedCondition}
                    className="btn-primary"
                  >
                    {loading ? "Loading..." : "Show suggestions"}
                  </button>
                </div>

                {treatment && (
                  <div className="mt-4 space-y-4">
                    <div className="text-xs text-gray-500">
                      {treatment.disclaimer}
                    </div>

                    {treatment.consult_doctor_alerts?.length > 0 && (
                      <div className="border border-red-200 bg-red-50 rounded p-4">
                        <div
                          className="symptom-section-title"
                          style={{ color: "#b42323" }}
                        >
                          Consult doctor / urgent care
                        </div>
                        <ul
                          className="list-disc pl-5"
                          style={{ color: "#b42323" }}
                        >
                          {treatment.consult_doctor_alerts.map((m, idx) => (
                            <li key={idx}>{m}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div>
                      <div className="font-semibold mb-2">
                        Basic OTC guidance
                      </div>
                      {treatment.otc?.length ? (
                        <div className="space-y-2">
                          {treatment.otc.map((m) => (
                            <div key={m.name} className="border rounded p-3">
                              <div className="font-semibold">{m.name}</div>
                              {m.use_for?.length > 0 && (
                                <div className="text-sm text-gray-700">
                                  Use for: {m.use_for.join(", ")}
                                </div>
                              )}
                              {m.adult_dose && (
                                <div className="text-sm text-gray-700">
                                  Adult dose: {m.adult_dose}
                                </div>
                              )}
                              {m.adult_max_per_day_mg && (
                                <div className="text-sm text-gray-700">
                                  Adult max/day: {m.adult_max_per_day_mg} mg
                                </div>
                              )}
                              {m.notes?.length > 0 && (
                                <ul className="list-disc pl-5 text-sm text-gray-700 mt-2">
                                  {m.notes.map((n, idx) => (
                                    <li key={idx}>{n}</li>
                                  ))}
                                </ul>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-gray-500">
                          No OTC guidance available for this condition.
                        </div>
                      )}
                    </div>

                    <div>
                      <div className="font-semibold mb-2">Home remedies</div>
                      {treatment.home_remedies?.length ? (
                        <ul className="list-disc pl-5 text-gray-700">
                          {treatment.home_remedies.map((h, idx) => (
                            <li key={idx}>{h}</li>
                          ))}
                        </ul>
                      ) : (
                        <div className="text-gray-500">
                          No home remedies listed.
                        </div>
                      )}
                    </div>

                    <div>
                      <div className="font-semibold mb-2">
                        Dosage awareness / safety
                      </div>
                      <ul className="list-disc pl-5 text-gray-700">
                        {(treatment.dosage_awareness || []).map((d, idx) => (
                          <li key={idx}>{d}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {nextQuestion?.question && (
            <div
              className="border rounded p-4"
              style={{ background: "#f4f7fb" }}
            >
              <div className="symptom-section-title">Follow-up question</div>
              <div className="mb-3">{nextQuestion.question}</div>
              <div className="symptom-actions">
                <button
                  type="button"
                  onClick={() => answerFollowUp(true)}
                  className="btn-primary"
                >
                  Yes
                </button>
                <button
                  type="button"
                  onClick={() => answerFollowUp(false)}
                  className="btn-secondary"
                >
                  No
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SymptomChecker;
