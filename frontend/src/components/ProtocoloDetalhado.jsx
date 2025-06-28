import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom"; // Adicionado useNavigate

function ProtocoloDetalhado() {
    const { id } = useParams();
    const [protocolo, setProtocolo] = useState(null);
    const [file, setFile] = useState(null);
    const [motivo, setMotivo] = useState("");
    const [error, setError] = useState("");
    const navigate = useNavigate(); // Substituído useHistory por useNavigate

    useEffect(() => {
        const token = localStorage.getItem("token");
        if (!token) {
            navigate("/login"); // Substituído history.push por navigate
            return;
        }

        fetch(`http://localhost:8000/api/protocolos/${id}`, {
            headers: { "Authorization": `Bearer ${token}` },
        })
            .then((res) => res.json())
            .then((data) => setProtocolo(data))
            .catch((err) => setError("Erro ao carregar protocolo"));
    }, [id, navigate]); // Atualizado para depender de navigate

    const handleDownload = () => {
        const token = localStorage.getItem("token");
        window.open(`http://localhost:8000/api/anexos/${protocolo.id_anexo}?token=${token}`, "_blank");
    };

    const handleUpload = async (e) => {
        e.preventDefault();
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await fetch(`http://localhost:8000/api/protocolos/${id}/upload`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` },
                body: formData,
            });
            if (res.ok) {
                alert("Recibo enviado com sucesso!");
                setFile(null);
            } else {
                setError("Erro ao enviar recibo");
            }
        } catch (err) {
            setError("Erro ao enviar recibo");
        }
    };

    const handleDivergencia = async (e) => {
        e.preventDefault();
        try {
            const res = await fetch(`http://localhost:8000/api/protocolos/${id}/divergencia`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("token")}`,
                },
                body: JSON.stringify({ motivo }),
            });
            if (res.ok) {
                alert("Divergência registrada com sucesso!");
                setMotivo("");
            } else {
                setError("Erro ao registrar divergência");
            }
        } catch (err) {
            setError("Erro ao registrar divergência");
        }
    };

    if (!protocolo) return <div className="text-center py-12">Carregando...</div>;
    if (error) return <div className="text-red-500 text-center py-12">{error}</div>;

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <h1 className="text-3xl font-bold text-gray-800 mb-6">Detalhes do Protocolo #{protocolo.id_email}</h1>
            <div className="bg-white shadow-lg rounded-lg p-6 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <p><strong>Assunto:</strong> {protocolo.assunto}</p>
                        <p><strong>Remetente:</strong> {protocolo.remetente}</p>
                        <p><strong>Recebido em:</strong> {protocolo.recebido_em}</p>
                        <p><strong>Processo:</strong> {protocolo.processo}</p>
                        <p><strong>OPAJ:</strong> {protocolo.opaj}</p>
                        <p><strong>Tribunal:</strong> {protocolo.tribunal}</p>
                    </div>
                    <div>
                        <p><strong>Ramo da Justiça:</strong> {protocolo.ramo_justica}</p>
                        <p><strong>Estado:</strong> {protocolo.estado}</p>
                        <p><strong>Prazo Fatal:</strong> {protocolo.prazo_fatal}</p>
                        <p><strong>Tipo de Resposta:</strong> {protocolo.tipo_resposta}</p>
                        <p><strong>Status Final:</strong> {protocolo.status_final}</p>
                        <p><strong>Situação IA:</strong> {protocolo.situacao_ia}</p>
                        <p><strong>Situação Manual:</strong> {protocolo.situacao_manual}</p>
                        <p><strong>Motivo:</strong> {protocolo.motivo}</p>
                    </div>
                </div>
                {protocolo.id_anexo && (
                    <div className="mt-4">
                        <button
                            onClick={handleDownload}
                            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                        >
                            Baixar Anexo ({protocolo.nome_anexo})
                        </button>
                    </div>
                )}
            </div>

            <div className="bg-white shadow-lg rounded-lg p-6 mb-6">
                <h2 className="text-xl font-semibold mb-4">Enviar Recibo de Protocolo</h2>
                <form onSubmit={handleUpload}>
                    <input
                        type="file"
                        accept=".pdf,.jpg,.png"
                        onChange={(e) => setFile(e.target.files[0])}
                        className="mb-4"
                    />
                    <button
                        type="submit"
                        disabled={!file}
                        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-300"
                    >
                        Enviar Recibo
                    </button>
                </form>
            </div>

            <div className="bg-white shadow-lg rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Registrar Divergência</h2>
                <form onSubmit={handleDivergencia}>
                    <textarea
                        value={motivo}
                        onChange={(e) => setMotivo(e.target.value)}
                        placeholder="Descreva o motivo da divergência..."
                        className="w-full border border-gray-300 p-2 rounded mb-4"
                        rows="4"
                    />
                    <button
                        type="submit"
                        disabled={!motivo}
                        className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 disabled:bg-gray-300"
                    >
                        Registrar Divergência
                    </button>
                </form>
            </div>
        </div>
    );
}

export default ProtocoloDetalhado;