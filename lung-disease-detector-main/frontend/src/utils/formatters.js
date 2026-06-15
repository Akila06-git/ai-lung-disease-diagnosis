import { format } from "date-fns";

export const formatDate = (value) => {
  if (!value) return "";
  const date = typeof value === "string" ? new Date(value) : value;
  return format(date, "dd MMM yyyy, HH:mm");
};

export const formatConfidence = (value) =>
  typeof value === "number" ? `${(value * 100).toFixed(2)}%` : "N/A";

export const truncateText = (text, maxLength = 80) => {
  if (!text) return "";
  return text.length > maxLength ? `${text.slice(0, maxLength)}…` : text;
};

export const capitalizeFirst = (text) =>
  text ? text.charAt(0).toUpperCase() + text.slice(1) : "";

