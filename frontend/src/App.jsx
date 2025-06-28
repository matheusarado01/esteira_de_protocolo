import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import Login from "./components/Login";
import TabelaPendentes from "./components/TabelaPendentes";
import TabelaProtocolados from "./components/TabelaProtocolados";
import TabelaReportados from "./components/TabelaReportados";
import DetalheOficio from "./components/DetalheOficio";

// Componente para rotas protegidas
function PrivateRoute({ children }) {
    const { token } = useAuth();
    return token ? children : <Navigate to="/login" />;
}

// Redirecionamento inteligente da raiz: manda para login se não autenticado, senão para pendentes
function RootRedirect() {
    const { token } = useAuth();
    return token ? <Navigate to="/pendentes" /> : <Navigate to="/login" />;
}

const App = () => (
    <AuthProvider>
        <Router>
            <Routes>
                {/* Login é sempre público */}
                <Route path="/login" element={<Login />} />
                {/* Rotas protegidas */}
                <Route
                    path="/pendentes"
                    element={
                        <PrivateRoute>
                            <TabelaPendentes />
                        </PrivateRoute>
                    }
                />
                <Route
                    path="/protocolados"
                    element={
                        <PrivateRoute>
                            <TabelaProtocolados />
                        </PrivateRoute>
                    }
                />
                <Route
                    path="/reportados"
                    element={
                        <PrivateRoute>
                            <TabelaReportados />
                        </PrivateRoute>
                    }
                />
                <Route
                    path="/oficio/:id_email"
                    element={
                        <PrivateRoute>
                            <DetalheOficio />
                        </PrivateRoute>
                    }
                />
                {/* Acesso raiz manda para pendentes ou login */}
                <Route path="/" element={<RootRedirect />} />
                {/* Qualquer outra rota não existente manda para login */}
                <Route path="*" element={<Navigate to="/login" />} />
            </Routes>
        </Router>
    </AuthProvider>
);

export default App;
