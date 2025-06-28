import React, { createContext, useContext, useState, useEffect } from "react";

const AuthContext = createContext();

export function useAuth() {
    return useContext(AuthContext);
}

export function AuthProvider({ children }) {
    const [token, setToken] = useState(() => localStorage.getItem("token"));
    const [user, setUser] = useState(() => localStorage.getItem("username") || "");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Sincroniza o contexto quando localStorage for alterado em outra aba/janela
        const handleStorage = () => setToken(localStorage.getItem("token"));
        window.addEventListener("storage", handleStorage);
        return () => window.removeEventListener("storage", handleStorage);
    }, []);

    const login = (token, username) => {
        localStorage.setItem("token", token);
        localStorage.setItem("username", username);
        setToken(token);
        setUser(username);
    };

    const logout = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("username");
        setToken(null);
        setUser("");
    };

    return (
        <AuthContext.Provider value={{ token, user, login, logout, loading, setLoading }}>
            {children}
        </AuthContext.Provider>
    );
}
