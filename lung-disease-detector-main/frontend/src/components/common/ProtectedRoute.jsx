import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

const ProtectedRoute = ({ children, requireAdmin = false }) => {
    const { user, loading } = useAuth();
    const location = useLocation();

    if (loading) {
        return (
            <div className="flex justify-center items-center h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    if (requireAdmin && !user.is_superuser && user.role !== 'DOCTOR') {
        return <Navigate to="/" replace />;
    }

    // Role check logic can be expanded here
    // if (requireDoctor && !user.roles.includes('Doctor')) ...

    return children;
};

export default ProtectedRoute;
