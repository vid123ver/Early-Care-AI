import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const Login = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login({ email, password });
      const to = location.state?.from || "/dashboard";
      navigate(to, { replace: true });
    } catch (err) {
      setError(err.response?.data?.message || "Login failed");
    }
    setLoading(false);
  };

  return (
    <div className="auth-page">
      <form onSubmit={handleSubmit} className="auth-card">
        <h2 className="auth-title">Welcome back to EarlyCare</h2>
        <div className="auth-subtitle">
          Sign in to view your health insights
        </div>
        {error && <div className="auth-alert-error">{error}</div>}
        <div className="mb-4">
          <label className="auth-field-label">Email</label>
          <input
            type="email"
            className="auth-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="mb-4">
          <label className="auth-field-label">Password</label>
          <input
            type="password"
            className="auth-input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <div style={{ textAlign: "right", marginTop: "-0.5rem", marginBottom: "1rem" }}>
          <Link className="auth-link" to="/forgot-password">
            Forgot password?
          </Link>
        </div>
        <button type="submit" className="auth-button" disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </button>
        <div className="auth-footer">
          Don&apos;t have an account?{" "}
          <Link className="auth-link" to="/register">
            Register
          </Link>
        </div>
      </form>
    </div>
  );
};

export default Login;
