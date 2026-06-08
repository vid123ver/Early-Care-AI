import axiosInstance from "./axiosInstance";

export const registerUser = (data) =>
  axiosInstance.post("/auth/register", data);

export const loginUser = (data) => axiosInstance.post("/auth/login", data);

export const requestPasswordReset = (data) =>
  axiosInstance.post("/auth/forgot-password", data);

export const confirmPasswordReset = (data) =>
  axiosInstance.post("/auth/reset-password", data);

export const getMe = () => axiosInstance.get("/auth/me");
