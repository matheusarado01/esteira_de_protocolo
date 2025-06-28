// src/components/TabelaProtocolados.jsx

import React, { useEffect, useState } from "react";

function TabelaProtocolados() {
  const [oficios, setOficios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");

  useEffect(() => {
    fetch("/api/oficios/protocolados")
      .then(res => res.json())
      .then(data => {
        setOficios(data.oficios_protocolados || []);
        setLoading(false);
      })
      .catch(() => {
        setErro("Erro ao buscar ofícios protocolados.");
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="p-4">Carregando...</div>;
  if (erro) return <div className="p-4 text-red-600">{erro}</div>;

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-3">Ofícios Protocolados</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white rounded shadow">
          <thead>
            <tr>
              <th className="py-2 px-4">Assunto</th>
              <th className="py-2 px-4">Remetente</th>
              <th className="py-2 px-4">Recebido em</th>
              <th className="py-2 px-4">Protocolado em</th>
              <th className="py-2 px-4">Usuário</th>
              <th className="py-2 px-4">Recibo</th>
              <th className="py-2 px-4">Anexos</th>
              <th className="py-2 px-4">Status</th>
            </tr>
          </thead>
          <tbody>
            {oficios.map(oficio => (
              <tr key={oficio.id_email} className="border-t hover:bg-gray-50">
                <td className="py-2 px-4">{oficio.assunto}</td>
                <td className="py-2 px-4">{oficio.remetente}</td>
                <td className="py-2 px-4">{new Date(oficio.recebido_em).toLocaleString()}</td>
                <td className="py-2 px-4">{oficio.data_protocolo ? new Date(oficio.data_protocolo).toLocaleString() : ""}</td>
                <td className="py-2 px-4">{oficio.usuario_protocolo}</td>
                <td className="py-2 px-4">
                  {oficio.recibo_nome ? (
                    <span className="text-gray-500">{oficio.recibo_nome}</span>
                    // Quando implementar download do recibo, faça um link aqui
                  ) : "—"}
                </td>
                <td className="py-2 px-4">
                  {(oficio.anexos || []).map(ax => (
                    <a
                      key={ax.id_anexo}
                      href={`/api/oficios/anexo/${ax.id_anexo}/download`}
                      className="text-blue-600 underline mr-2"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {ax.nome_arquivo}
                    </a>
                  ))}
                </td>
                <td className="py-2 px-4">{oficio.status_final}</td>
              </tr>
            ))}
            {oficios.length === 0 && (
              <tr>
                <td colSpan={8} className="text-center py-6 text-gray-400">Nenhum ofício protocolado.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TabelaProtocolados;
