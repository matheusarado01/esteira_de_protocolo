import React, { useEffect, useState } from "react";

const PainelControle = () => {
  const [log, setLog] = useState("");
  const [casos, setCasos] = useState([]);
  const [totalPendentes, setTotalPendentes] = useState(0);
  const [progresso, setProgresso] = useState(null);
  const [capturaAtiva, setCapturaAtiva] = useState(false);
  const [dataCaptura, setDataCaptura] = useState("");
  const [limiteCaptura, setLimiteCaptura] = useState(10);
  const [limiteIA, setLimiteIA] = useState(10);
  const [dataIA, setDataIA] = useState("");
  const [executandoIA, setExecutandoIA] = useState(false);
  const [pipelinePausado, setPipelinePausado] = useState(false);

  const token = localStorage.getItem("token");

  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const capturarEmails = async () => {
    if (capturaAtiva) {
      setLog("⚠️ Captura já em andamento.");
      return;
    }
    setCapturaAtiva(true);
    setLog("⏳ Iniciando captura de e-mails...");
    setProgresso({ total: 1, atual: 0 });

    try {
      const params = new URLSearchParams();
      if (limiteCaptura) params.append("limite", limiteCaptura);
      if (dataCaptura) params.append("data", dataCaptura);

      const res = await fetch(`/api/captura-emails?${params.toString()}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setLog(data.mensagem || "Captura finalizada.");
    } catch (e) {
      setLog("❌ Erro ao iniciar captura.");
    }

    await delay(2000);
    verificarProgresso();
    carregarCasos();
    setCapturaAtiva(false);
  };

  const pararCaptura = async () => {
    try {
      const res = await fetch("/api/captura-emails/stop", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setLog(data.mensagem || "Captura interrompida.");
    } catch (e) {
      setLog("❌ Erro ao tentar parar a captura.");
    }
  };

  const executarIA = async () => {
    setExecutandoIA(true);
    setLog("🤖 Rodando validação IA...");

    try {
      const params = new URLSearchParams();
      if (limiteIA) params.append("limite", limiteIA);
      if (dataIA) params.append("data", dataIA);

      const res = await fetch(`/api/validar-ia?${params.toString()}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setLog(data.mensagem || "Validação finalizada.");
    } catch (e) {
      setLog("❌ Erro ao rodar IA.");
    }

    await delay(1000);
    carregarCasos();
    setExecutandoIA(false);
  };

  const verificarProgresso = () => {
    fetch("/api/captura-emails/progresso", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => {
        if (!data || data.total === 0 || data.finalizado) {
          setProgresso(null);
          setCapturaAtiva(false);
        } else {
          setProgresso(data);
          setCapturaAtiva(true);
        }
      })
      .catch(() => {
        setProgresso(null);
        setCapturaAtiva(false);
      });
  };

  const carregarCasos = () => {
    fetch("/api/painel-controle/casos-em-processamento", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => {
        // DEBUG: Veja o que vem da API
        console.log("RESPOSTA DA API casos-em-processamento:", data);

        // Tenta várias chaves conhecidas, ou usa array direto
        if (Array.isArray(data.casos)) setCasos(data.casos);
        else if (Array.isArray(data.esteira)) setCasos(data.esteira);
        else if (Array.isArray(data.protocolos)) setCasos(data.protocolos);
        else if (Array.isArray(data)) setCasos(data);
        else setCasos([]);
      })
      .catch(() => setCasos([]));

    fetch("/api/painel-controle/contagem-casos", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => setTotalPendentes(data.total || 0))
      .catch(() => setTotalPendentes(0));
  };

  // --- Pipeline pause/resume logic
  const atualizarStatusPipeline = async () => {
    const res = await fetch("/api/pipeline/status");
    const data = await res.json();
    setPipelinePausado(data.pausado);
  };

  const alternarPipeline = async () => {
    const rota = pipelinePausado ? "retomar" : "pausar";
    const res = await fetch(`/api/pipeline/${rota}`, { method: "POST" });
    const data = await res.json();
    setLog(data.mensagem);
    atualizarStatusPipeline();
  };

  useEffect(() => {
    carregarCasos();
    verificarProgresso();
    atualizarStatusPipeline();
  }, []);

  useEffect(() => {
    if (!progresso) return;
    const interval = setInterval(() => {
      verificarProgresso();
    }, 2000);
    return () => clearInterval(interval);
  }, [progresso]);

  // STYLE SHORTCUT
  const fullBtn =
    "w-full px-4 py-2 rounded font-semibold text-white text-base transition-all duration-150 shadow-sm";
  const inputBox = "border px-2 py-1 rounded text-base w-[120px]";

  return (
    <div className="p-8 space-y-8 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
        <span role="img" aria-label="brain">🧠</span> Painel de Controle
      </h1>

      {/* Cards em linha */}
      <div className="flex flex-col md:flex-row gap-4">
        {/* Card Captura */}
        <div className="flex-1 p-4 border rounded-xl shadow bg-white flex flex-col items-center justify-between min-w-[290px] max-w-[360px]">
          <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <span role="img" aria-label="email">📨</span> Captura de E-mails
          </h2>
          {/* Inputs centralizados */}
          <div className="flex gap-3 justify-center mb-3 w-full">
            <input
              type="date"
              value={dataCaptura}
              onChange={e => setDataCaptura(e.target.value)}
              className={inputBox}
            />
            <input
              type="number"
              value={limiteCaptura}
              min={1}
              onChange={e => setLimiteCaptura(Number(e.target.value))}
              className={inputBox + " w-[70px]"}
              placeholder="Limite"
            />
          </div>
          {/* Botões centralizados, largura total */}
          <div className="flex gap-3 w-full">
            <button
              onClick={capturarEmails}
              disabled={capturaAtiva}
              className={fullBtn + " bg-blue-600 hover:bg-blue-700 disabled:opacity-50"}
            >
              Capturar
            </button>
            <button
              onClick={pararCaptura}
              className={fullBtn + " bg-red-600 hover:bg-red-700"}
            >
              Parar
            </button>
          </div>
          {capturaAtiva && (
            <span className="mt-2 text-xs text-yellow-700 font-medium animate-pulse text-center w-full">
              🔄 Captura em andamento...
            </span>
          )}
        </div>

        {/* Card Validação IA */}
        <div className="flex-1 p-4 border rounded-xl shadow bg-white flex flex-col items-center justify-between min-w-[290px] max-w-[430px]">
          <h2 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <span role="img" aria-label="robot">🤖</span> Validação IA
          </h2>
          <div className="flex gap-3 justify-center mb-3 w-full">
            <input
              type="date"
              value={dataIA}
              onChange={e => setDataIA(e.target.value)}
              className={inputBox}
            />
            <input
              type="number"
              value={limiteIA}
              min={1}
              onChange={e => setLimiteIA(Number(e.target.value))}
              className={inputBox + " w-[70px]"}
              placeholder="Limite"
            />
          </div>
          <div className="flex gap-3 w-full">
            <button
              onClick={executarIA}
              disabled={executandoIA || pipelinePausado}
              className={fullBtn + (executandoIA || pipelinePausado
                ? " bg-gray-400 text-white cursor-not-allowed"
                : " bg-green-600 hover:bg-green-700")}
            >
              {executandoIA ? "Executando..." : "Executar IA"}
            </button>
            <button
              onClick={alternarPipeline}
              className={fullBtn + (pipelinePausado
                ? " bg-green-600 hover:bg-green-700"
                : " bg-red-600 hover:bg-red-700")}
            >
              {pipelinePausado ? "Retomar" : "Pausar"}
            </button>
          </div>
          {pipelinePausado && (
            <div className="mt-2 text-xs text-red-700 font-medium w-full text-center">
              ⚠️ Pipeline pausado. Nenhuma validação será executada até ser retomado.
            </div>
          )}
        </div>
      </div>

      {/* LOG */}
      {log && <div className="mt-2 p-3 bg-gray-100 rounded border text-base">{log}</div>}

      {/* BARRA DE PROGRESSO */}
      {progresso && progresso.total > 0 && (
        <div className="mt-4 max-w-lg">
          <div className="text-sm mb-1">
            Progresso: {progresso.atual} de {progresso.total}
          </div>
          <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
            <div
              className="bg-blue-600 h-full transition-all duration-300"
              style={{
                width: `${(progresso.atual / progresso.total) * 100}%`,
              }}
            />
          </div>
        </div>
      )}

      {/* TABELA DE CASOS */}
      <div className="mt-10">
        <h3 className="text-lg font-bold mb-2">Casos aguardando validação</h3>
        <div className="mb-3">
          <span className="inline-flex items-center gap-2 px-3 py-1 bg-yellow-100 text-yellow-800 text-sm rounded">
            📊 {totalPendentes} casos pendentes de validação
          </span>
        </div>
        {Array.isArray(casos) && casos.length === 0 ? (
          <p className="text-sm text-gray-600">Nenhum caso pendente no momento.</p>
        ) : (
          <div className="overflow-auto bg-white rounded shadow">
            <table className="w-full border text-sm">
              <thead>
                <tr className="bg-gray-100 text-left">
                  <th className="px-2 py-1">ID</th>
                  <th className="px-2 py-1">Assunto</th>
                  <th className="px-2 py-1">Chegada</th>
                  <th className="px-2 py-1">Status IA</th>
                </tr>
              </thead>
              <tbody>
                {Array.isArray(casos) && casos.map((caso) => (
                  <tr key={caso.id_resposta || caso.id_protocolo || caso.id_email} className="border-t">
                    <td className="px-2 py-1">{caso.id_resposta || caso.id_protocolo || caso.id_email}</td>
                    <td className="px-2 py-1">{caso.assunto?.slice(0, 80)}</td>
                    <td className="px-2 py-1">
                      {caso.data_chegada
                        ? new Date(caso.data_chegada).toLocaleString()
                        : caso.criado_em
                        ? new Date(caso.criado_em).toLocaleString()
                        : ""}
                    </td>
                    <td className="px-2 py-1">
                      {caso.status_validacao || caso.status || "⏳ Aguardando"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default PainelControle;
