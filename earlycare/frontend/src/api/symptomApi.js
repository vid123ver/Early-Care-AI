import axiosInstance from "./axiosInstance";

export const checkSymptoms = (payload) =>
  axiosInstance.post("/symptom/check", payload);

