import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  confirmPasswordReset,
  requestPasswordReset,
} from "../api/authApi";

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleRequestReset = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const res = await requestPasswordReset({ email });
      const token = res?.data?.reset_token;
      setMessage(
        token
          ? `Reset code created. Copy this code: ${token}`
          : res.data?.message || "Reset code created.",
      );
      if (token) setResetToken(token);
    } catch (err) {
      setError(err.response?.data?.message || "Could not create reset code");
    }
    setLoading(false);
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setMessage("");
    try {
      const res = await confirmPasswordReset({
        email,
        reset_token: resetToken,
        new_password: newPassword,
      });
      setMessage(res.data?.message || "Password updated successfully");
      setResetToken("");
      setNewPassword("");
    } catch (err) {
      setError(err.response?.data?.message || "Could not reset password");
    }
    setLoading(false);
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h2 className="auth-title">Reset your password</h2>
        <div className="auth-subtitle">
          Request a reset code, then set a new password
        </div>

        {error && <div className="auth-alert-error">{error}</div>}
        {message && <div className="auth-alert-success">{message}</div>}

        <form onSubmit={handleRequestReset}>
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
          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? "Creating code..." : "Get reset code"}
          </button>
        </form>

        <form onSubmit={handleResetPassword} style={{ marginTop: "1.5rem" }}>
          <div className="mb-4">
            <label className="auth-field-label">Reset code</label>
            <input
              type="text"
              className="auth-input"
              value={resetToken}
              onChange={(e) => setResetToken(e.target.value)}
              placeholder="Paste the reset code here"
              required
            />
          </div>
          <div className="mb-4">
            <label className="auth-field-label">New password</label>
            <input
              type="password"
              className="auth-input"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? "Updating..." : "Reset password"}
          </button>
        </form>

        <div className="auth-footer">
          Remembered it?{" "}
          <Link className="auth-link" to="/login">
            Back to login
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;