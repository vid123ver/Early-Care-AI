import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./App.css";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import MainLayout from "./layouts/MainLayout";
import Dashboard from "./pages/Dashboard.jsx";
import ReportUpload from "./pages/ReportUpload.jsx";
import ReportHistory from "./pages/ReportHistory.jsx";
import ReportDetails from "./pages/ReportDetails.jsx";
import ReportChat from "./pages/ReportChat.jsx";
import SymptomChecker from "./pages/SymptomChecker.jsx";
import DietGuide from "./pages/DietGuide.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import ForgotPassword from "./pages/ForgotPassword.jsx";
import { AuthProvider } from "./auth/AuthContext.jsx";
import ProtectedRoute from "./auth/ProtectedRoute.jsx";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <Routes>
                    <Route path="dashboard" element={<Dashboard />} />
                    <Route path="upload" element={<ReportUpload />} />
                    <Route path="history" element={<ReportHistory />} />
                    <Route
                      path="history/:reportId"
                      element={<ReportDetails />}
                    />
                    <Route
                      path="chat"
                      element={<ReportChat reportId={null} />}
                    />
                    <Route path="symptoms" element={<SymptomChecker />} />
                    <Route path="diet" element={<DietGuide />} />
                    <Route
                      path="*"
                      element={<Navigate to="/dashboard" replace />}
                    />
                  </Routes>
                </MainLayout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  </StrictMode>,
);
