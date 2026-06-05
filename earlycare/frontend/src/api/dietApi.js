import apiClient from "./axiosInstance";

export const getDietRecommendation = (payload) =>
  apiClient.post("/diet/recommend", payload);
