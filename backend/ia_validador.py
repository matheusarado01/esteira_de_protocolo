import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def prompt_formal_ia(assunto, corpo, nomes_anexos, textos_anexos, campos_extraidos):
    return f"""
Você é um assistente jurídico especializado na gestão de ofícios judiciais de uma instituição financeira de abrangência nacional. O setor de Gerência de Ofícios (GOF) é responsável por receber e responder ordens judiciais encaminhadas por juízes de todo o Brasil, que podem requerer informações detalhadas, envio de documentos (extrato, contrato, termo, comprovante, etc.) ou ações concretas (bloqueio/desbloqueio de valores, transferência, liberação de gravame, etc).

Seu papel é **validar a formalidade da resposta** (e-mail, anexos, minuta) para o protocolo, indicando de forma clara se está APTO para protocolo, deve ser REVISADO, ou REJEITADO.

**Atenção:**  
- Sempre inicie sua resposta com: "AÇÃO: Protocolar.", "AÇÃO: Revisar.", ou "AÇÃO: Rejeitar."  
- Logo em seguida, justifique de forma objetiva sua decisão.  
- Finalize explicando, em frase única, o que o banco está efetivamente respondendo ou cumprindo neste caso.

### Dados recebidos:
- Assunto do e-mail: "{assunto}"
- Corpo do e-mail: "{corpo[:800]}"
- Nomes dos anexos recebidos: {nomes_anexos}
- Resumo dos anexos (prévia do texto): {textos_anexos}

### Campos extraídos do assunto/processamento automático:
{json.dumps(campos_extraidos, ensure_ascii=False)}

### Critérios práticos:
- O nome da minuta de resposta do anexo deve bater com os identificadores do assunto e/ou conteúdo.
- Os identificadores do assunto (processo, FNDA, DILA, status) devem estar presentes no título/conteúdo dos anexos ou no texto da resposta.
- Se o corpo ou a minuta mencionam "segue anexo", "documento em anexo", "assinatura em anexo", o respectivo documento deve estar anexo.
- Se o status é "resposta final", deve haver informação conclusiva ou documento atendendo à ordem judicial. Diga qual é.
- Se status é "dilação", a minuta deve conter pedido de dilação de prazo.
- Não repita informações. Seja conciso e objetivo.

### Perguntas para análise (responda na justificativa, mas NÃO repita as perguntas!):
1. Explique sucintamente o que o banco está informando ou cumprindo na resposta.
2. Todos os nomes de anexos são compatíveis com o que está descrito no assunto?
3. Todos os identificadores do assunto aparecem corretamente nos anexos ou no texto?
4. Faltam anexos ou documentos obrigatórios (minuta, comprovante de assinatura, documento citado, etc)?
5. Há inconsistências formais ou entre menção e presença de anexos?

Responda obrigatoriamente em JSON, conforme exemplo:

{{
  "valido": true,
  "campos_faltantes": [],
  "coerencia": true,
  "motivo": "AÇÃO: Protocolar. Minuta de resposta identificada, todos os identificadores conferem, e comprovante de assinatura está anexo. O banco presta informação sobre bloqueio judicial e anexa extratos conforme determinação.",
  "acao_sugerida": "protocolar"
}}
"""

def validar_formal_ia(assunto, corpo, nomes_anexos, textos_anexos, campos_extraidos, model="gpt-4o"):
    prompt = prompt_formal_ia(assunto, corpo, nomes_anexos, textos_anexos, campos_extraidos)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Você é um assistente jurídico validador formal de ofícios bancários."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response.choices[0].message.content.strip()

        # Corrige formatação em markdown tipo ```json\n...\n```
        if content.startswith("```json"):
            content = re.sub(r"^```json\s*", "", content)
        if content.endswith("```"):
            content = re.sub(r"\s*```$", "", content)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "valido": False,
                "campos_faltantes": [],
                "coerencia": False,
                "motivo": f"Resposta da IA inválida: não foi possível interpretar como JSON. Conteúdo: {content}",
                "acao_sugerida": "revisar"
            }
    except Exception as e:
        return {
            "valido": False,
            "campos_faltantes": [],
            "coerencia": False,
            "motivo": f"Erro ao chamar a API da IA: {str(e)}",
            "acao_sugerida": "revisar"
        }
