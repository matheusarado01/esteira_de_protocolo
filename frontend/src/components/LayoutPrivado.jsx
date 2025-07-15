import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";

const menu = [
  { path: "/pendentes", label: "📋", title: "Esteira de Protocolo" },
  { path: "/painel-controle", label: "🧠", title: "Painel de Controle" },
  { path: "/relatorios", label: "📊", title: "Relatórios" },
];

const LayoutPrivado = ({ children }) => {
  const [colapsado, setColapsado] = useState(false);
  const location = useLocation();

  return (
    <div className="flex h-screen">
      {/* Menu lateral */}
      <aside className={`bg-white border-r shadow transition-all duration-300 ${colapsado ? "w-16" : "w-64"} flex flex-col`}>
        <div className="flex items-center justify-between p-4 border-b">
          {!colapsado && <h2 className="font-bold text-lg">Menu</h2>}
          <button onClick={() => setColapsado(!colapsado)} className="text-gray-500 hover:text-black">
            {colapsado ? "➡️" : "⬅️"}
          </button>
        </div>

        <nav className="flex-1 p-2 space-y-2">
          {menu.map(item => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center space-x-2 px-3 py-2 rounded hover:bg-blue-100 transition ${location.pathname === item.path ? "bg-blue-200 font-semibold" : ""}`}
            >
              <span className="text-xl">{item.label}</span>
              {!colapsado && <span>{item.title}</span>}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Conteúdo principal */}
      <main className="flex-1 overflow-y-auto bg-gray-50 p-4">
        {children}
      </main>
    </div>
  );
};

export default LayoutPrivado;
