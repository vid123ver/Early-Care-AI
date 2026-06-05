import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { getMe, loginUser } from "../api/authApi";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const setTokenAndPersist = (t) => {
    if (t) {
      localStorage.setItem("token", t);
      setToken(t);
    } else {
      localStorage.removeItem("token");
      setToken(null);
    }
  };

  const logout = () => {
    setTokenAndPersist(null);
    setUser(null);
  };

  const login = async ({ email, password }) => {
    const res = await loginUser({ email, password });
    const t = res?.data?.token;
    if (!t) throw new Error("No token returned from server");
    setTokenAndPersist(t);
    const meRes = await getMe();
    setUser(meRes.data);
    return meRes.data;
  };

  useEffect(() => {
    let cancelled = false;
    const bootstrap = async () => {
      setLoading(true);
      const existingToken = localStorage.getItem("token");
      if (!existingToken) {
        if (!cancelled) {
          setToken(null);
          setUser(null);
          setLoading(false);
        }
        return;
      }
      try {
        const meRes = await getMe();
        if (!cancelled) {
          setToken(existingToken);
          setUser(meRes.data);
        }
      } catch (e) {
        if (!cancelled) {
          setTokenAndPersist(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token && user),
      loading,
      login,
      logout,
      setUser,
    }),
    [token, user, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};

