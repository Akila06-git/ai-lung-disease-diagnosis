import React from "react";
import { Routes, Route } from "react-router-dom";
import Upload from "@components/Upload";
import History from "@components/History";
import Result from "@components/Result";
import Dashboard from "@components/Dashboard";
import Navbar from "@components/common/Navbar";
import ErrorBoundary from "@components/common/ErrorBoundary";

import { AuthProvider } from "./context/AuthContext";
import Login from "./components/Auth/Login";
import Register from "./components/Auth/Register";

import ProtectedRoute from "./components/common/ProtectedRoute";

const App = () => {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-background text-slate-100">
        <Navbar />
        <main className="max-w-6xl mx-auto px-4 py-8">
          <ErrorBoundary>
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />

              {/* Protected Routes (Doctors/Authenticated) */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <Upload />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/history"
                element={
                  <ProtectedRoute>
                    <History />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/result/:id"
                element={
                  <ProtectedRoute>
                    <Result />
                  </ProtectedRoute>
                }
              />

              {/* Admin Routes (Superuser only) */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute requireAdmin={true}>
                    <Dashboard />
                  </ProtectedRoute>
                }
              />
            </Routes>
          </ErrorBoundary>
        </main>
      </div>
    </AuthProvider>
  );
};

export default App;

