// src/AuthContext.jsx

import React, { createContext, useContext, useState, useEffect } from "react";
import { API_BASE } from "./config";

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [user, setUser] = useState(() => localStorage.getItem("username") || "");
  const [loading, setLoading] = useState(true); // INICIA COMO TRUE

  // Escuta outras abas
  useEffect(() => {
    const handleStorage = () => {
      setToken(localStorage.getItem("token"));
      setUser(localStorage.getItem("username") || "");
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  // Valida o token com a API
  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    const validarToken = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/user/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!res.ok) throw new Error("Token inválido");
        const data = await res.json();
        setUser(data.username || data.name || "usuário");
      } catch (err) {
        logout(); // limpa token se inválido
      } finally {
        setLoading(false);
      }
    };

    validarToken();
  }, [token]);

  const login = (newToken, username) => {
    localStorage.setItem("token", newToken);
    localStorage.setItem("username", username);
    setToken(newToken);
    setUser(username);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    setToken(null);
    setUser("");
    setLoading(false);
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout, loading, setLoading }}>
      {children}
    </AuthContext.Provider>
  );
}
