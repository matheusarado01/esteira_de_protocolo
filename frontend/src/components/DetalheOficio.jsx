import React, { useEffect, useState } from "react";
import axios from "axios";
import { API_BASE } from "../config";

const DetalheOficio = ({ id_email, onClose }) => {
  const [detalhe, setDetalhe] = useState(null);
  const [erro, setErro] = useState(null);
  const token = localStorage.getItem("token");

  useEffect(() => {
    async function fetchDetalhe() {
      try {
        const response = await axios.get(`${API_BASE}/api/oficios/${id_email}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setDetalhe(response.data);
      } catch (err) {
        setErro("Erro ao carregar detalhes.");
      }
    }

    fetchDetalhe();
  }, [id_email, token]);

  const baixarAnexo = async (idAnexo, nomeArquivo) => {
    try {
      const response = await axios.get(`${API_BASE}/api/oficios/anexo/${idAnexo}/download`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = nomeArquivo;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (error) {
      alert("Erro ao baixar anexo.");
    }
  };

  if (!detalhe) return <div className="p-6">Carregando detalhes...</div>;
  const { email, respostas, anexos, protocolos } = detalhe;

  return (
    <div className="fixed inset-0 z-50 flex justify-center items-center bg-black bg-opacity-40">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-3xl relative space-y-6 overflow-y-auto max-h-[90vh]">
        <button className="absolute top-2 right-2 text-gray-500" onClick={onClose}>✕</button>
        <h2 className="text-xl font-bold">📄 Detalhes do Ofício</h2>

        <div>
          <p><strong>Assunto:</strong> {email.assunto}</p>
          <p><strong>Remetente:</strong> {email.remetente}</p>
          <p><strong>Recebido em:</strong> {new Date(email.recebido_em).toLocaleString("pt-BR")}</p>
          <p><strong>Corpo:</strong></p>
          <pre className="bg-gray-100 rounded p-2 text-sm">{email.corpo_email}</pre>
        </div>

        <div>
          <h3 className="font-bold mb-1">📎 Anexos</h3>
          {anexos.length > 0 ? (
            <ul className="list-disc ml-5 text-blue-600 text-sm">
              {anexos.map(ax => (
                <li key={ax.id_anexo}>
                  <button onClick={() => baixarAnexo(ax.id_anexo, ax.nome_arquivo)} className="hover:underline">
                    {ax.nome_arquivo}
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">Nenhum anexo disponível.</p>
          )}
        </div>

        <div>
          <h3 className="font-bold mb-1">📬 Respostas</h3>
          {respostas.length > 0 ? (
            <ul className="list-disc ml-5 text-sm">
              {respostas.map((r, idx) => (
                <li key={idx}>
                  <strong>Status:</strong> {r.status_final} | <strong>Processo:</strong> {r.processo} | <strong>OPAJ:</strong> {r.opaj}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">Nenhuma resposta registrada.</p>
          )}
        </div>

        <div>
          <h3 className="font-bold mb-1">✅ Protocolos</h3>
          {protocolos.length > 0 ? (
            <ul className="list-disc ml-5 text-sm">
              {protocolos.map((p, idx) => (
                <li key={idx}>
                  <strong>Usuário:</strong> {p.usuario || p.responsavel} |
                  <strong> Data:</strong> {new Date(p.data_registro).toLocaleString("pt-BR")} |
                  <strong> Ação:</strong> {p.acao_usuario}
                  {p.nome_arquivo && (
                    <> | <button onClick={() => baixarAnexo(p.id_protocolo, p.nome_arquivo)} className="text-blue-600 hover:underline">{p.nome_arquivo}</button></>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">Nenhum protocolo registrado.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default DetalheOficio;
