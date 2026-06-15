import React, { createContext, useState, useEffect, useContext } from "react";
import api from "../services/api";
import { jwtDecode } from "jwt-decode";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check for tokens on mount
        const accessToken = localStorage.getItem("accessToken");
        if (accessToken) {
            try {
                const decoded = jwtDecode(accessToken);
                // Check if token is expired
                if (decoded.exp * 1000 < Date.now()) {
                    localStorage.removeItem("accessToken");
                    localStorage.removeItem("refreshToken");
                    setUser(null);
                } else {
                    setUser({ username: decoded.username || decoded.user_id, ...decoded });
                }
            } catch (e) {
                console.error("Invalid token:", e);
                localStorage.removeItem("accessToken");
                localStorage.removeItem("refreshToken");
                setUser(null);
            }
        }
        setLoading(false);
    }, []);

    const login = async (username, password) => {
        try {
            const response = await api.post("/auth/login/", { username, password });
            const { access, refresh } = response.data;

            localStorage.setItem("accessToken", access);
            localStorage.setItem("refreshToken", refresh);

            const decoded = jwtDecode(access);
            setUser({ username: decoded.username || decoded.user_id, ...decoded });
            return { success: true };
        } catch (error) {
            console.error("Login failed:", error);
            return {
                success: false,
                error: error.response?.data?.detail || "Login failed. Please check your credentials."
            };
        }
    };

    const register = async (username, email, password, role) => {
        try {
            await api.post("/auth/register/", { username, email, password, role });
            return { success: true };
        } catch (error) {
            console.error("Registration failed:", error);
            return {
                success: false,
                error: error.response?.data?.username?.[0] || "Registration failed."
            };
        }
    };

    const logout = () => {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, register, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
