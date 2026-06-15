/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#020617",
        surface: "#0f172a",
        primary: {
          50: "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",
          600: "#2563eb",
          700: "#1d4ed8",
          800: "#1e40af",
          900: "#1e3a8a",
          950: "#172554",
        },
        danger: {
          500: "#ef4444",
          600: "#dc2626",
          700: "#b91c1c",
        },
        success: {
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
        },
        warning: {
          500: "#f97316",
          600: "#ea580c",
          700: "#c2410c",
        },
        info: {
          500: "#06b6d4",
          600: "#0891b2",
          700: "#0e7490",
        }
      },
      boxShadow: {
        card: "0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)",
        premium: "0 0 20px rgba(59, 130, 246, 0.15)"
      }
    }
  },
  plugins: []
};

