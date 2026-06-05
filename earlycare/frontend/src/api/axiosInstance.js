import axios from "axios";

const axiosInstance = axios.create({
  baseURL: "http://localhost:5002",
});

axiosInstance.interceptors.request.use((req) => {
  const token = localStorage.getItem("token");
  if (token) {
    req.headers.Authorization = `Bearer ${token}`;
  }
  return req;
});

export default axiosInstance;
