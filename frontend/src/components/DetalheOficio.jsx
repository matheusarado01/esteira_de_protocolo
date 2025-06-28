// src/components/DetalheOficio.jsx

import React, { useEffect, useState } from "react";

function DetalheOficio({ id_email, onClose }) {
  const [detalhe, setDetalhe] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/oficios/${id_email}`)
      .then(res => res.json())
      .then(setDetalhe)
      .finally(() => setLoading(false));
  }, [id_email]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-2xl relative">
        <button className="absolute top-2 right-2 text-gray-500" onClick={onClose}>✕</button>
        <h3 className="text-xl font-bold mb-2">Detalhes do Ofício</h3>
        {loading && <p>Carregando...</p>}
        {detalhe && (
          <div>
            <div className="mb-2"><b>Assunto:</b> {detalhe.assunto}</div>
            <div className="mb-2"><b>Remetente:</b> {detalhe.remetente}</div>
            <div className="mb-2"><b>Recebido em:</b> {new Date(detalhe.recebido_em).toLocaleString()}</div>
            <div className="mb-2"><b>Corpo do E-mail:</b><br />{detalhe.corpo_email}</div>
            <div className="mb-2"><b>Análise IA:</b> {detalhe.acao_sugerida} / {detalhe.motivo} / Coerência: {String(detalhe.coerencia)}</div>
            <div className="mb-2"><b>Status:</b> {detalhe.status_final}</div>
            <div className="mb-2">
              <b>Anexos:</b><br />
              {(detalhe.anexos || []).map(ax => (
                <a
                  key={ax.id_anexo}
                  href={`/api/oficios/anexo/${ax.id_anexo}/download`}
                  className="text-blue-600 underline mr-3"
                  target="_blank"
                  rel="noopener noreferrer"
                >{ax.nome_arquivo}</a>
              ))}
            </div>
            {detalhe.protocolos && detalhe.protocolos.length > 0 && (
              <div className="mb-2">
                <b>Protocolos:</b>
                <ul>
                  {detalhe.protocolos.map(p => (
                    <li key={p.id_protocolo}>
                      {p.acao_usuario} por {p.usuario} em {new Date(p.data_registro).toLocaleString()}
                      {p.nome_arquivo && (
                        <a
                          href="#"
                          onClick={e => {
                            e.preventDefault();
                            alert("Download do recibo ainda não implementado (endp. download protocolo)");
                          }}
                          className="ml-2 text-blue-500 underline"
                        >{p.nome_arquivo}</a>
                      )}
                      {p.motivo_manual && <span className="ml-2 text-xs text-red-500">Motivo: {p.motivo_manual}</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default DetalheOficio;
