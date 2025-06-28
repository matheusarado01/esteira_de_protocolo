import React, { useState } from "react";
import { useNavigate } from "react-router-dom"; // Substituído useHistory por useNavigate

function Relatorios() {
    const [dataInicio, setDataInicio] = useState("");
    const [dataFim, setDataFim] = useState("");
    const [tribunal, setTribunal] = useState("");
    const [status, setStatus] = useState("");
    const [error, setError] = useState("");
    const navigate = useNavigate(); // Substituído useHistory por useNavigate

    const handleExport = async (e) => {
        e.preventDefault();
        const token = localStorage.getItem("token");
        if (!token) {
            navigate("/login"); // Substituído history.push por navigate
            return;
        }

        try {
            const params = new URLSearchParams({
                ...(dataInicio && { data_inicio: dataInicio }),
                ...(dataFim && { data_fim: dataFim }),
                ...(tribunal && { tribunal }),
                ...(status && { status }),
            });
            const res = await fetch(`http://localhost:8000/api/relatorios?${params}`, {
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
                            <label className="block text-gray-700 mb-2" htmlFor="dataInicio">
                                Data Início
                            </label>
                            <input
                                type="date"
                                id="dataInicio"
                                value={dataInicio}
                                onChange={(e) => setDataInicio(e.target.value)}
                                className="w-full border border-gray-300 p-2 rounded focus:outline-none focus:ring focus:border-blue-300"
                            />
                        </div>
                        <div>
                            <label className="block text-gray-700 mb-2" htmlFor="dataFim">
                                Data Fim
                            </label>
                            <input
                                type="date"
                                id="dataFim"
                                value={dataFim}
                                onChange={(e) => setDataFim(e.target.value)}
                                className="w-full border border-gray-300 p-2 rounded focus:outline-none focus:ring focus:border-blue-300"
                            />
                        </div>
                        <div>
                            <label className="block text-gray-700 mb-2" htmlFor="tribunal">
                                Tribunal
                            </label>
                            <select
                                id="tribunal"
                                value={tribunal}
                                onChange={(e) => setTribunal(e.target.value)}
                                className="w-full border border-gray-300 p-2 rounded focus:outline-none focus:ring focus:border-blue-300"
                            >
                                <option value="">Todos</option>
                                <option value="TJSP">TJSP</option>
                                <option value="TRT">TRT</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-gray-700 mb-2" htmlFor="status">
                                Status
                            </label>
                            <select
                                id="status"
                                value={status}
                                onChange={(e) => setStatus(e.target.value)}
                                className="w-full border border-gray-300 p-2 rounded focus:outline-none focus:ring focus:border-blue-300"
                            >
                                <option value="">Todos</option>
                                <option value="EM CORREÇÃO">Em Correção</option>
                                <option value="FINALIZADO">Finalizado</option>
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