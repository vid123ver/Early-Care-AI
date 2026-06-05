import axiosInstance from "./axiosInstance";

export const uploadReport = (formData) =>
  axiosInstance.post("/pdf/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const getPredictions = () => axiosInstance.get("/user/predictions");

export const getReports = () => axiosInstance.get("/user/reports");

export const getReport = (reportId) => axiosInstance.get(`/user/reports/${reportId}`);
