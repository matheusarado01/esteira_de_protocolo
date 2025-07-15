import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE } from "../config";

function Relatorios() {
    const [dataInicio, setDataInicio] = useState("");
    const [dataFim, setDataFim] = useState("");
    const [tribunal, setTribunal] = useState("");
    const [status, setStatus] = useState("");
    const [error, setError] = useState("");
    const navigate = useNavigate();

    const handleExport = async (e) => {
        e.preventDefault();
        const token = localStorage.getItem("token");
        if (!token) {
            navigate("/login");
            return;
        }

        try {
            const params = new URLSearchParams({
                ...(dataInicio && { data_inicio: dataInicio }),
                ...(dataFim && { data_fim: dataFim }),
                ...(tribunal && { tribunal }),
                ...(status && { status }),
            });

            const res = await fetch(`${API_BASE}/api/protocolos/relatorios?${params}`, {
                headers: { "Authorization": `Bearer ${token}` },
            });

            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "relatorio_protocolos.xlsx";
                document.body.appendChild(a);
                a.click();
                a.remove();
            } else {
                setError("Erro ao gerar relatório");
            }
        } catch (err) {
            setError("Erro ao conectar ao servidor");
        }
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <h1 className="text-3xl font-bold text-gray-800 mb-6">Relatórios</h1>
            <div className="bg-white shadow-lg rounded-lg p-6">
                <form onSubmit={handleExport}>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                            <label className="block text-gray-700">Data Início</label>
                            <input
                                type="date"
                                value={dataInicio}
                                onChange={(e) => setDataInicio(e.target.value)}
                                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                            />
                        </div>
                        <div>
                            <label className="block text-gray-700">Data Fim</label>
                            <input
                                type="date"
                                value={dataFim}
                                onChange={(e) => setDataFim(e.target.value)}
                                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                            />
                        </div>
                        <div>
                            <label className="block text-gray-700">Tribunal</label>
                            <input
                                type="text"
                                value={tribunal}
                                onChange={(e) => setTribunal(e.target.value)}
                                placeholder="Ex: TJSP, TRF3"
                                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                            />
                        </div>
                        <div>
                            <label className="block text-gray-700">Status</label>
                            <select
                                value={status}
                                onChange={(e) => setStatus(e.target.value)}
                                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                            >
                                <option value="">Todos</option>
                                <option value="pendente">Pendente</option>
                                <option value="protocolado">Protocolado</option>
                                <option value="reprovado">Reprovado</option>
                                <option value="reportado">Reportado</option>
                            </select>
                        </div>
                    </div>

                    {error && <p className="text-red-500 mb-4">{error}</p>}

                    <button
                        type="submit"
                        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                    >
                        Exportar Relatório (Excel)
                    </button>
                </form>
            </div>
        </div>
    );
}

export default Relatorios;
