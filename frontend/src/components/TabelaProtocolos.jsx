import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom"; // Adicionado useNavigate

function TabelaProtocolos() {
    const [protocolos, setProtocolos] = useState([]);
    const [filtro, setFiltro] = useState("");
    const [error, setError] = useState("");
    const navigate = useNavigate(); // Substituído useHistory por useNavigate

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (!token) {
            navigate("/login"); // Substituído history.push por navigate
            return;
        }

        fetch("http://localhost:8000/api/protocolos", {
            headers: { "Authorization": `Bearer ${token}` },
        })
            .then((res) => res.json())
            .then((data) => setProtocolos(data.protocolos || []))
            .catch((err) => setError("Erro ao buscar dados: " + err.message));
    }, [navigate]); // Atualizado para depender de navigate

    const protocolosFiltrados = protocolos.filter(
        (protocolo) =>
            protocolo.assunto?.toLowerCase().includes(filtro.toLowerCase()) ||
            protocolo.remetente?.toLowerCase().includes(filtro.toLowerCase()) ||
            protocolo.processo?.toLowerCase().includes(filtro.toLowerCase())
    );

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
                Esteira de Protocolo · GOF
            </h1>
            <p className="text-gray-500 mb-6">Esteira de Protocolos GOF</p>

            <div className="mb-4">
                <Link
                    to="/relatorios"
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                >
                    Gerar Relatório
                </Link>
            </div>

            <div className="bg-white p-4 shadow rounded mb-6">
                <div className="flex items-center gap-2">
                    <span role="img" aria-label="lupa">🔍</span>
                    <input
                        type="text"
                        placeholder="Buscar por assunto, remetente ou processo"
                        value={filtro}
                        onChange={(e) => setFiltro(e.target.value)}
                        className="flex-1 border border-gray-300 p-2 rounded focus:outline-none focus:ring focus:border-blue-300"
                    />
                </div>
            </div>

            {error && <p className="text-red-500 mb-4">{error}</p>}

            <div className="overflow-x-auto rounded shadow">
                <table className="min-w-full bg-white">
                    <thead className="bg-blue-600 text-white">
                        <tr>
                            <th className="px-6 py-3 text-left text-sm font-semibold">ID Email</th>
                            <th className="px-6 py-3 text-left text-sm font-semibold">Assunto</th>
                            <th className="px-6 py-3 text-left text-sm font-semibold">Remetente</th>
                            <th className="px-6 py-3 text-left text-sm font-semibold">Recebido em</th>
                            <th className="px-6 py-3 text-left text-sm font-semibold">Processo</th>
                            <th className="px-6 py-3 text-left text-sm font-semibold">Tribunal</th>
                            <th className="px-6 py-3 text-left text-sm font-semibold">Status Final</th>
                        </tr>
                    </thead>
                    <tbody className="text-gray-700">
                        {protocolosFiltrados.length === 0 ? (
                            <tr>
                                <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                                    Nenhum resultado encontrado.
                                </td>
                            </tr>
                        ) : (
                            protocolosFiltrados.map((protocolo) => (
                                <tr key={protocolo.id_email} className="hover:bg-gray-50">
                                    <td className="px-6 py-4">{protocolo.id_email}</td>
                                    <td className="px-6 py-4">
                                        <Link to={`/protocolos/${protocolo.id_email}`}>
                                            {protocolo.assunto}
                                        </Link>
                                    </td>
                                    <td className="px-6 py-4">{protocolo.remetente}</td>
                                    <td className="px-6 py-4">{protocolo.recebido_em}</td>
                                    <td className="px-6 py-4">{protocolo.processo}</td>
                                    <td className="px-6 py-4">{protocolo.tribunal}</td>
                                    <td className="px-6 py-4">{protocolo.status_final}</td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}

export default TabelaProtocolos;