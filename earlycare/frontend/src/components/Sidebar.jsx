import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  FaTachometerAlt,
  FaFileMedical,
  FaComments,
  FaHistory,
  FaUserMd,
  FaSignOutAlt,
} from "react-icons/fa";
import { useAuth } from "../auth/AuthContext";

const navItems = [
  { label: "Dashboard", path: "/dashboard", icon: <FaTachometerAlt /> },
  { label: "Report Upload", path: "/upload", icon: <FaFileMedical /> },
  { label: "Report Chat", path: "/chat", icon: <FaComments /> },
  { label: "Report History", path: "/history", icon: <FaHistory /> },
  { label: "Symptom Checker", path: "/symptoms", icon: <FaUserMd /> },
  { label: "Diet Guide", path: "/diet", icon: <FaFileMedical /> },
];

const Sidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <FaUserMd className="sidebar-logo" />
        <h2>EarlyCare</h2>
      </div>
      {user?.email && (
        <div style={{ padding: "0 16px 12px", color: "#5b6b7a", fontSize: 13 }}>
          Signed in as
          <div style={{ fontWeight: 700, color: "#2b8be6" }}>{user.email}</div>
        </div>
      )}
      <nav>
        <ul>
          {navItems.map((item) => (
            <li
              key={item.path}
              className={location.pathname === item.path ? "active" : ""}
            >
              <Link to={item.path}>
                <span className="icon">{item.icon}</span>
                <span className="nav-label">{item.label}</span>
              </Link>
            </li>
          ))}
          <li>
            <button
              type="button"
              onClick={handleLogout}
              style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "12px 14px",
                background: "transparent",
                border: "none",
                cursor: "pointer",
                color: "#e35d5d",
                fontWeight: 700,
              }}
            >
              <span className="icon">
                <FaSignOutAlt />
              </span>
              <span className="nav-label">Logout</span>
            </button>
          </li>
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;
