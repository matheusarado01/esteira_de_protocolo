import React, { useState, useEffect } from "react";
import DetalheOficio from "./DetalheOficio";
import UploadRecibo from "./UploadRecibo";
import ReportarDivergencia from "./ReportarDivergencia";
import { useAuth } from "../AuthContext";
import { API_BASE } from "../config";

const STATUS_LABELS = {
  pending: "Pendente",
  protocolado: "Protocolado",
  invalid: "Inválido IA",
  incompleto: "Incompleto",
  reportado: "Reportado",
  revisao: "Em Revisão",
  completed: "Concluído",
};

const STATUS_COLOR = {
  pending: "bg-gray-500 text-white",
  protocolado: "bg-green-600 text-white",
  invalid: "bg-red-600 text-white",
  incompleto: "bg-yellow-400 text-black",
  reportado: "bg-red-600 text-white",
  revisao: "bg-orange-500 text-white",
  completed: "bg-green-800 text-white",
  default: "bg-blue-200 text-black"
};

function TabelaEsteira() {
  const [protocolos, setProtocolos] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");
  const [detalhe, setDetalhe] = useState(null);
  const [reciboModal, setReciboModal] = useState(null);
  const [reportarModal, setReportarModal] = useState(null);
  const [expandido, setExpandido] = useState(null);

  const [filtroData, setFiltroData] = useState("");
  const [filtroStatus, setFiltroStatus] = useState("");
  const [filtroTipoEmail, setFiltroTipoEmail] = useState("protocolo");
  const [filtroIa, setFiltroIa] = useState("");
  const { token } = useAuth();

  // Fetch protocolos da esteira
  useEffect(() => {
    if (!token) return;

    setLoading(true);
    setErro("");

    let url = `${API_BASE}/api/esteira?`;
    if (filtroData) url += `data=${filtroData}&`;
    if (filtroStatus) url += `status=${filtroStatus}&`;
    if (filtroTipoEmail) url += `tipo_email=${filtroTipoEmail}&`;
    if (filtroIa) url += `acao_ia=${filtroIa}&`;

    fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(res => {
        if (!res.ok) throw new Error("Erro ao buscar dados");
        return res.json();
      })
      .then(data => setProtocolos(data.esteira || []))
      .catch(() => setErro("Erro ao buscar protocolos da esteira."))
      .finally(() => setLoading(false));
  }, [token, filtroData, filtroStatus, filtroTipoEmail, filtroIa]);

  const iaAcoes = Array.from(new Set(protocolos.map(o => o.acao_sugerida).filter(Boolean)));
  const tiposEmail = Array.from(new Set(protocolos.map(o => o.tipo_email).filter(Boolean)));

  const corBadge = status => STATUS_COLOR[status] || STATUS_COLOR.default;

  if (!token) {
    return <div className="p-6 text-red-600">🔒 Você precisa estar logado para acessar a esteira.</div>;
  }

  return (
    <div className="p-6 space-y-4">
      <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">🛤️ Esteira de Protocolos</h2>

      {/* Filtros */}
      <div className="flex flex-wrap gap-2 items-end mb-4">
        <div>
          <label className="block text-xs font-bold text-gray-600">Data:</label>
          <input type="date" value={filtroData} onChange={e => setFiltroData(e.target.value)} className="border px-2 py-1 rounded text-sm" />
        </div>
        <div>
          <label className="block text-xs font-bold text-gray-600">Status:</label>
          <select value={filtroStatus} onChange={e => setFiltroStatus(e.target.value)} className="border px-2 py-1 rounded text-sm">
            <option value="">Todos</option>
            {Object.keys(STATUS_LABELS).map(st => (
              <option key={st} value={st}>{STATUS_LABELS[st]}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-bold text-gray-600">Tipo:</label>
          <select value={filtroTipoEmail} onChange={e => setFiltroTipoEmail(e.target.value)} className="border px-2 py-1 rounded text-sm">
            <option value="">Todos</option>
            {tiposEmail.map((tp, i) => (
              <option key={i} value={tp}>{tp[0].toUpperCase() + tp.slice(1)}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-bold text-gray-600">Classificação IA:</label>
          <select value={filtroIa} onChange={e => setFiltroIa(e.target.value)} className="border px-2 py-1 rounded text-sm">
            <option value="">Todas</option>
            {iaAcoes.map((ia, i) => (
              <option key={i} value={ia}>{ia}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="text-sm text-gray-600">
        Mostrando <strong>{protocolos.length}</strong> resultado(s) para o filtro aplicado.
      </div>

      {loading ? (
        <div className="p-6 text-sm">⏳ Carregando esteira...</div>
      ) : erro ? (
        <div className="p-6 text-red-600">{erro}</div>
      ) : protocolos.length === 0 ? (
        <div className="text-center text-gray-500 py-20">Nenhum caso encontrado para o filtro.</div>
      ) : (
        <div className="flex flex-col gap-4">
          {protocolos.map((protocolo) => (
            <div
              key={protocolo.id_protocolo || protocolo.id_email}
              className={`bg-white border border-gray-300 rounded-lg shadow-sm p-4 w-full cursor-pointer hover:bg-gray-50 transition`}
              onClick={() => setExpandido(expandido === protocolo.id_protocolo ? null : protocolo.id_protocolo)}
            >
              <div className="flex items-center gap-2 mb-2">
                {protocolo.status && (
                  <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${corBadge(protocolo.status)}`}>
                    {STATUS_LABELS[protocolo.status] || protocolo.status}
                  </span>
                )}
                {protocolo.tipo_email && (
                  <span className="ml-2 px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-700 border border-gray-300">
                    {protocolo.tipo_email}
                  </span>
                )}
              </div>
              <div className="flex flex-col sm:flex-row sm:justify-between">
                <div className="font-semibold text-sm text-gray-800">{protocolo.assunto}</div>
                <div className="text-xs text-gray-500">{new Date(protocolo.recebido_em).toLocaleString()}</div>
              </div>
              <div className="text-xs text-gray-700 mt-1">
                <strong>Remetente:</strong> {protocolo.remetente} | <strong>Status:</strong> {STATUS_LABELS[protocolo.status] || protocolo.status}
              </div>

              {/* Campos críticos */}
              <div className="text-xs text-gray-700 mt-1 flex flex-wrap gap-4">
                {protocolo.numero_processo && <span><strong>Processo:</strong> {protocolo.numero_processo}</span>}
                {protocolo.opaj && <span><strong>OPAJ:</strong> {protocolo.opaj}</span>}
                {protocolo.fnda && <span><strong>FNDA:</strong> {protocolo.fnda}</span>}
                {protocolo.tipo_origem && <span><strong>Tipo:</strong> {protocolo.tipo_origem}</span>}
                {protocolo.destinatario && <span><strong>Destinatário:</strong> {protocolo.destinatario}</span>}
                {protocolo.unidade_destino && <span><strong>Unidade:</strong> {protocolo.unidade_destino}</span>}
                {protocolo.tipo_resposta && <span><strong>Tipo de resposta:</strong> {protocolo.tipo_resposta}</span>}
              </div>

              {expandido === protocolo.id_protocolo && (
                <div className="mt-4 text-sm text-gray-800 space-y-3">
                  <div>
                    <p><strong>Ação IA:</strong> {protocolo.acao_sugerida || "—"}</p>
                    <p><strong>Motivo IA:</strong> {protocolo.motivo || "—"}</p>
                    <p><strong>Confiança IA:</strong> {String(protocolo.coerencia) || "—"}</p>
                    {protocolo.motivo_invalido && <p className="text-red-600"><strong>Motivo reporte:</strong> {protocolo.motivo_invalido}</p>}
                  </div>
                  <div>
                    <p className="font-semibold">Anexos:</p>
                    <ul className="list-disc ml-5 text-blue-600 text-sm">
                      {Array.isArray(protocolo.anexos) && protocolo.anexos.length > 0 ? (
                        protocolo.anexos.map((anexo, idx) => (
                          <li key={idx}>
                            <button
                              onClick={e => {
                                e.stopPropagation();
                                window.open(`${API_BASE.replace("/api", "")}/download-anexo/${anexo.id_anexo}`, "_blank");
                              }}
                              className="hover:underline"
                            >
                              📎 {anexo.nome_arquivo}
                            </button>
                          </li>
                        ))
                      ) : (
                        <li className="text-gray-400">Nenhum anexo disponível.</li>
                      )}
                    </ul>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    <button onClick={e => { e.stopPropagation(); setDetalhe(protocolo); }} className="bg-gray-100 hover:bg-gray-200 text-xs rounded px-3 py-1">Detalhar</button>
                    {["pending", "invalid", "incompleto", "revisao"].includes(protocolo.status) && (
                      <button onClick={e => { e.stopPropagation(); setReciboModal(protocolo); }} className="bg-blue-600 hover:bg-blue-700 text-white text-xs rounded px-3 py-1">Protocolar</button>
                    )}
                    <button onClick={e => { e.stopPropagation(); setReportarModal(protocolo); }} className="bg-red-500 hover:bg-red-600 text-white text-xs rounded px-3 py-1">Reportar</button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {detalhe && <DetalheOficio id_protocolo={detalhe.id_protocolo} onClose={() => setDetalhe(null)} />}
      {reciboModal && <UploadRecibo oficio={reciboModal} onClose={() => setReciboModal(null)} onSucesso={() => window.location.reload()} />}
      {reportarModal && <ReportarDivergencia oficio={reportarModal} onClose={() => setReportarModal(null)} onSucesso={() => window.location.reload()} />}
    </div>
  );
}

export default TabelaEsteira;
