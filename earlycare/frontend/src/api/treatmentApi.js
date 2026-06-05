import axiosInstance from "./axiosInstance";

export const getTreatmentSuggestions = (payload) =>
  axiosInstance.post("/treatment/suggest", payload);

