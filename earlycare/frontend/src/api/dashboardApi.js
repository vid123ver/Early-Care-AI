import axiosInstance from "./axiosInstance";

export const getDashboardOverview = (params) =>
  axiosInstance.get("/dashboard/overview", { params });

export const getHealthTrends = () =>
  axiosInstance.get("/dashboard/health_trends");

export const getAlerts = () => axiosInstance.get("/dashboard/alerts");

export const getLifestyle = () => axiosInstance.get("/dashboard/lifestyle");
