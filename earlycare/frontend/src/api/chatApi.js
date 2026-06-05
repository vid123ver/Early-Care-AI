import axiosInstance from "./axiosInstance";

export const uploadChatReport = (formData) =>
  axiosInstance.post("/chat/upload_report", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const askReportQuestion = (data) =>
  axiosInstance.post("/chat/ask", data);
