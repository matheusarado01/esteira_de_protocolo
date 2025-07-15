// src/components/ReportarDivergencia.jsx

import React, { useState } from "react";
import { API_BASE } from "../config"; // NOVO: importa a base da API

function ReportarDivergencia({ oficio, onClose, onSucesso }) {
  const [usuario, setUsuario] = useState("");
  const [motivo, setMotivo] = useState("");
  const [obs, setObs] = useState("");
  const [erro, setErro] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = e => {
    e.preventDefault();
    if (!motivo) return setErro("Informe o motivo da divergência.");
    setErro("");
    setLoading(true);

    const formData = new FormData();
    formData.append("usuario", usuario || "usuario");
    formData.append("motivo_manual", motivo);
    formData.append("observacao", obs);

    fetch(`${API_BASE}/api/oficios/${oficio.id_email}/reportar`, {
      method: "POST",
      body: formData,
    })
      .then(res => res.json())
      .then(data => {
        if (data.message) {
          onSucesso();
        } else {
          setErro(data.detail || "Erro ao reportar divergência.");
        }
      })
      .catch(() => setErro("Erro de conexão."))
      .finally(() => setLoading(false));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md relative">
        <button className="absolute top-2 right-2 text-gray-500" onClick={onClose}>✕</button>
        <h3 className="text-lg font-bold mb-3">Reportar Divergência</h3>
        <form onSubmit={handleSubmit}>
          <div className="mb-2">
            <label className="block mb-1 text-sm font-semibold">Usuário</label>
            <input value={usuario} onChange={e => setUsuario(e.target.value)} className="border rounded px-2 py-1 w-full" required />
          </div>
          <div className="mb-2">
            <label className="block mb-1 text-sm font-semibold">Motivo da Divergência</label>
            <textarea value={motivo} onChange={e => setMotivo(e.target.value)} className="border rounded px-2 py-1 w-full" rows={3} required />
          </div>
          <div className="mb-2">
            <label className="block mb-1 text-sm font-semibold">Observação</label>
            <input value={obs} onChange={e => setObs(e.target.value)} className="border rounded px-2 py-1 w-full" />
          </div>
          {erro && <div className="text-red-500 mb-2">{erro}</div>}
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300">Cancelar</button>
            <button type="submit" className="px-3 py-1 rounded bg-red-600 text-white hover:bg-red-700" disabled={loading}>
              {loading ? "Enviando..." : "Reportar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ReportarDivergencia;
