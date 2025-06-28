// src/components/TabelaPendentes.jsx

import React, { useState, useEffect } from "react";
import DetalheOficio from "./DetalheOficio";
import UploadRecibo from "./UploadRecibo";
import ReportarDivergencia from "./ReportarDivergencia";

function TabelaPendentes() {
  const [oficios, setOficios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState("");
  const [detalhe, setDetalhe] = useState(null);
  const [reciboModal, setReciboModal] = useState(null);
  const [reportarModal, setReportarModal] = useState(null);

  const carregarOficios = () => {
    fetch("/api/oficios/pendentes")
      .then(res => {
        if (!res.ok || res.status === 304) throw new Error("Sem conteúdo");
        return res.json();
      })
      .then(data => {
        setOficios(data.oficios_pendentes || []);
        setLoading(false);
      })
      .catch(() => {
        setErro("Erro ao buscar ofícios.");
        setLoading(false);
      });
  };

  useEffect(() => {
    carregarOficios();
  }, []);

  if (loading) return <div className="p-4">Carregando...</div>;
  if (erro) return <div className="p-4 text-red-600">{erro}</div>;

  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-3">Ofícios Pendentes de Protocolo</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white rounded shadow">
          <thead>
            <tr>
              <th className="py-2 px-4">Assunto</th>
              <th className="py-2 px-4">Remetente</th>
              <th className="py-2 px-4">Recebido em</th>
              <th className="py-2 px-4">Anexos</th>
              <th className="py-2 px-4">Análise IA</th>
              <th className="py-2 px-4">Status</th>
              <th className="py-2 px-4">Ações</th>
            </tr>
          </thead>
          <tbody>
            {oficios.map(oficio => (
              <tr key={oficio.id_email} className="border-t hover:bg-gray-50">
                <td className="py-2 px-4">{oficio.assunto}</td>
                <td className="py-2 px-4">{oficio.remetente}</td>
                <td className="py-2 px-4">{new Date(oficio.recebido_em).toLocaleString()}</td>
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
                <td className="py-2 px-4">
                  <div>
                    <span className="block font-semibold">Ação: {oficio.acao_sugerida}</span>
                    <span className="block text-xs">Motivo: {oficio.motivo_ia}</span>
                    <span className="block text-xs">Coerência: {String(oficio.coerencia_ia)}</span>
                  </div>
                </td>
                <td className="py-2 px-4">{oficio.status_final}</td>
                <td className="py-2 px-4">
                  <button
                    onClick={() => setDetalhe(oficio)}
                    className="mr-2 px-2 py-1 bg-gray-200 rounded hover:bg-gray-300 text-xs"
                  >
                    Detalhes
                  </button>
                  <button
                    onClick={() => setReciboModal(oficio)}
                    className="mr-2 px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-xs"
                  >
                    Protocolar
                  </button>
                  <button
                    onClick={() => setReportarModal(oficio)}
                    className="px-2 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-xs"
                  >
                    Reportar
                  </button>
                </td>
              </tr>
            ))}
            {oficios.length === 0 && (
              <tr>
                <td colSpan={7} className="text-center py-6 text-gray-400">Nenhum ofício pendente.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal Detalhe */}
      {detalhe && (
        <DetalheOficio
          id_email={detalhe.id_email}
          onClose={() => setDetalhe(null)}
        />
      )}

      {/* Modal Upload Recibo */}
      {reciboModal && (
        <UploadRecibo
          oficio={reciboModal}
          onClose={() => setReciboModal(null)}
          onSucesso={() => {
            setReciboModal(null);
            setLoading(true);
            carregarOficios();
          }}
        />
      )}

      {/* Modal Reportar Divergência */}
      {reportarModal && (
        <ReportarDivergencia
          oficio={reportarModal}
          onClose={() => setReportarModal(null)}
          onSucesso={() => {
            setReportarModal(null);
            setLoading(true);
            carregarOficios();
          }}
        />
      )}
    </div>
  );
}

export default TabelaPendentes;
