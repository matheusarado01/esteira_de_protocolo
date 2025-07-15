import React, { useState } from "react";
import { API_BASE } from "../config";
import { useAuth } from "../AuthContext";

function UploadRecibo({ oficio, onClose, onSucesso }) {
  const [file, setFile] = useState(null);
  const [obs, setObs] = useState("");
  const [erro, setErro] = useState("");
  const [loading, setLoading] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  const [mensagem, setMensagem] = useState("");

  const { user } = useAuth();

  const handleSubmit = async e => {
    e.preventDefault();
    if (!file) return setErro("Selecione um recibo para anexar.");
    setErro("");
    setLoading(true);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("responsavel", user);
    formData.append("observacao", obs);

    try {
      const res = await fetch(`${API_BASE}/api/oficios/${oficio.id_email}/protocolar`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data.message || data.mensagem) {
        const agora = new Date().toLocaleString("pt-BR");
        setMensagem(`✅ Protocolo realizado com sucesso por ${user} em ${agora}!`);
        setSucesso(true);
        setTimeout(() => {
          setSucesso(false);
          onSucesso();
          onClose();
        }, 2000);
      } else {
        setErro(data.detail || "Erro ao protocolar.");
      }
    } catch (err) {
      setErro("Erro de conexão.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md relative">
        <button className="absolute top-2 right-2 text-gray-500" onClick={onClose}>✕</button>
        <h3 className="text-lg font-bold mb-3">Protocolar Ofício</h3>
        <form onSubmit={handleSubmit}>
          {sucesso && (
            <div className="mb-3 p-3 rounded bg-green-200 text-green-900 font-bold border border-green-600 shadow flex items-center gap-2">
              ✅ {mensagem}
            </div>
          )}
          <div className="mb-2">
            <label className="block mb-1 text-sm font-semibold">Recibo (PDF ou imagem)</label>
            <input type="file" accept="application/pdf,image/*" onChange={e => setFile(e.target.files[0])} className="w-full" required />
          </div>
          <div className="mb-2">
            <label className="block mb-1 text-sm font-semibold">Observação</label>
            <input value={obs} onChange={e => setObs(e.target.value)} className="border rounded px-2 py-1 w-full" />
          </div>
          {erro && <div className="text-red-500 mb-2">{erro}</div>}
          <div className="flex justify-end gap-2">
            <button type="button" onClick={onClose} className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300">Cancelar</button>
            <button type="submit" className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700" disabled={loading || sucesso}>
              {loading ? "Enviando..." : "Protocolar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default UploadRecibo;
