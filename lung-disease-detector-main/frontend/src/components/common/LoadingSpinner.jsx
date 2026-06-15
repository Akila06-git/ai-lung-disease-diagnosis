import React from "react";
import PropTypes from "prop-types";

const sizeMap = {
  sm: "h-4 w-4",
  md: "h-6 w-6",
  lg: "h-8 w-8"
};

const LoadingSpinner = ({ size = "md", overlay = false, label = "Loading" }) => {
  const spinner = (
    <div
      className="flex flex-col items-center justify-center gap-2 text-slate-300"
      role="status"
      aria-label={label}
    >
      <svg
        className={`animate-spin text-blue-500 ${sizeMap[size]}`}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
        />
      </svg>
      <span className="text-xs">{label}</span>
    </div>
  );

  if (!overlay) {
    return spinner;
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-950/70">
      {spinner}
    </div>
  );
};

LoadingSpinner.propTypes = {
  size: PropTypes.oneOf(["sm", "md", "lg"]),
  overlay: PropTypes.bool,
  label: PropTypes.string
};

export default LoadingSpinner;

