import axios from "axios";
import toast from "react-hot-toast";

const api = axios.create({
  baseURL: "/api",
  withCredentials: false,
  timeout: 300000
});

api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error?.response?.data?.detail ||
      error?.response?.data?.error ||
      error.message ||
      "Unexpected error, please try again.";
    toast.error(message);
    return Promise.reject(error);
  }
);

// Add a request interceptor to include the JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("accessToken");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const uploadImage = (file, extraData = {}) => {
  const formData = new FormData();
  formData.append("image", file);
  if (extraData) {
    Object.entries(extraData).forEach(([key, value]) => {
      // Only append if value is present
      if (value !== undefined && value !== null && value !== "") {
        formData.append(key, value);
      }
    });
  }
  return api.post("/predict/", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
};

export const getTaskStatus = (taskId, predictionId) =>
  api.get(`/task/${taskId}/`, { params: predictionId ? { prediction_id: predictionId } : {} });

export const getPredictionHistory = (params) =>
  api.get("/predictions/", { params });

export const getRecommendations = (diseaseName) =>
  api.get(`/recommendations/${encodeURIComponent(diseaseName)}/`);

export const submitFeedback = (predictionId, trueClass) =>
  api.post(`/predictions/${predictionId}/feedback/`, { true_class: trueClass });

export const getDashboardStats = () =>
  api.get("/dashboard/stats/").then((res) => res.data);

export const retrainModel = () =>
  api.post("/admin/retrain/").then((res) => res.data);

export const downloadReport = (predictionId) =>
  api.get(`/predictions/${predictionId}/report/`, {
    responseType: "blob",
  });


export default api;
