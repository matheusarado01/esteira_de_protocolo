// src/App.jsx

import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import Login from "./components/Login";
import TabelaEsteira from "./components/Tabelaesteira";
import TabelaProtocolados from "./components/TabelaProtocolados";
import TabelaReportados from "./components/TabelaReportados";
import DetalheOficio from "./components/DetalheOficio";
import Relatorios from "./components/Relatorios";
import PainelControle from "./components/PainelControle";
import LayoutPrivado from "./components/LayoutPrivado";

// Componente para proteger rotas com layout
function PrivateRoute({ children, withLayout = true }) {
  const { token, loading } = useAuth();

  if (loading) return <div className="p-6 text-sm">⏳ Verificando autenticação...</div>;

  if (!token) return <Navigate to="/login" replace />;

  return withLayout ? <LayoutPrivado>{children}</LayoutPrivado> : children;
}

// Redirecionamento da rota raiz "/"
function RootRedirect() {
  const { token, loading } = useAuth();

  if (loading) return <div className="p-6 text-sm">⏳ Carregando...</div>;

  return token ? <Navigate to="/pendentes" replace /> : <Navigate to="/login" replace />;
}

const App = () => (
  <AuthProvider>
    <Router>
      <Routes>
        {/* Login (pública) */}
        <Route path="/login" element={<Login />} />

        {/* Rotas protegidas com layout */}
        <Route path="/pendentes" element={<PrivateRoute><TabelaEsteira /></PrivateRoute>} />
        <Route path="/protocolados" element={<PrivateRoute><TabelaProtocolados /></PrivateRoute>} />
        <Route path="/reportados" element={<PrivateRoute><TabelaReportados /></PrivateRoute>} />
        <Route path="/relatorios" element={<PrivateRoute><Relatorios /></PrivateRoute>} />
        <Route path="/painel-controle" element={<PrivateRoute><PainelControle /></PrivateRoute>} />

        {/* Detalhes de ofício → SEM layout */}
        <Route path="/oficio/:id_email" element={
          <PrivateRoute withLayout={false}>
            <DetalheOficio />
          </PrivateRoute>
        } />

        {/* Rota raiz e fallback */}
        <Route path="/" element={<RootRedirect />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Router>
  </AuthProvider>
);

export default App;
