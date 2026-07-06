import json
import os
import re
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

load_dotenv(ROOT_DIR / ".env")


SYSTEM_PROMPT = """
Você é o Mentor de Estudos IA, um assistente educacional especializado em organização de estudos para concursos de segurança pública.

Sua função é ajudar o usuário a entender como estudar, priorizar conteúdos, organizar revisões, usar questões, simulados e caderno de erros.

Você deve responder apenas com base na base de conhecimento fornecida no projeto.

Regras:
1. Não invente informações sobre editais, datas, salários, bancas, requisitos ou legislação atualizada.
2. Quando a pergunta depender de informação oficial recente, oriente o usuário a consultar o edital oficial.
3. Não prometa aprovação.
4. Não ofereça diagnóstico psicológico, médico, jurídico ou financeiro.
5. Não colete dados pessoais sensíveis.
6. Seja direto, didático, motivador e profissional.
7. Sempre que possível, entregue uma próxima ação prática.
8. Quando não houver informação suficiente na base, diga claramente que não possui dados suficientes.
9. Use linguagem em português do Brasil.
10. Evite respostas longas demais.
"""


STOPWORDS = {
    "a", "o", "os", "as", "um", "uma", "de", "do", "da", "dos", "das", "em", "no",
    "na", "nos", "nas", "para", "por", "com", "que", "eu", "me", "minha", "meu",
    "como", "qual", "quais", "quando", "onde", "e", "ou", "se", "ao", "à", "às",
    "ser", "ter", "vou", "posso", "preciso"
}


@st.cache_data(show_spinner=False)
def carregar_base():
    with open(DATA_DIR / "faq_estudos.json", "r", encoding="utf-8") as f:
        faq = json.load(f)

    with open(DATA_DIR / "trilhas_estudo.json", "r", encoding="utf-8") as f:
        trilhas = json.load(f)

    regras = (DATA_DIR / "regras_seguranca.md").read_text(encoding="utf-8")

    return faq, trilhas, regras


def normalizar(texto: str) -> list[str]:
    texto = texto.lower()
    texto = re.sub(r"[^a-zà-ú0-9\s]", " ", texto)
    termos = [t for t in texto.split() if t not in STOPWORDS and len(t) > 2]
    return termos


def contem_termo(texto: str, termo: str) -> bool:
    if " " in termo:
        return termo in texto
    return re.search(rf"\b{re.escape(termo)}\b", texto) is not None


def buscar_contexto(pergunta: str, faq: list[dict], limite: int = 3) -> list[dict]:
    termos = set(normalizar(pergunta))
    resultados = []

    for item in faq:
        conteudo = " ".join([
            item.get("categoria", ""),
            item.get("pergunta", ""),
            item.get("resposta", ""),
            " ".join(item.get("tags", [])),
        ])
        termos_item = set(normalizar(conteudo))
        score = len(termos.intersection(termos_item))
        if score > 0:
            resultados.append((score, item))

    resultados.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in resultados[:limite]]


def pergunta_pede_dado_atualizado(pergunta: str) -> bool:
    termos_criticos = [
        "edital", "data da prova", "salário", "salario", "vagas", "banca", "resultado",
        "inscrição", "inscricao", "taxa", "requisito", "idade máxima", "idade maxima",
        "cronograma oficial", "último edital", "ultimo edital", "mais recente",
        "próximo concurso", "proximo concurso", "2026", "2027"
    ]
    p = pergunta.lower()
    return any(contem_termo(p, t) for t in termos_criticos)


def pergunta_pede_dado_sensivel(pergunta: str) -> bool:
    termos_sensiveis = [
        "cpf", "rg", "endereço", "endereco", "telefone", "cartão", "cartao",
        "senha", "dados bancários", "dados bancarios"
    ]
    p = pergunta.lower()
    return any(contem_termo(p, t) for t in termos_sensiveis)


def pergunta_pede_promessa_aprovacao(pergunta: str) -> bool:
    termos_promessa = [
        "garante", "garantir", "garantia", "aprovação", "aprovacao",
        "vou passar", "certeza que passo", "certeza de passar"
    ]
    p = pergunta.lower()
    return any(contem_termo(p, t) for t in termos_promessa)


def gerar_resposta(pergunta: str, faq: list[dict], trilhas: dict) -> tuple[str, list[dict]]:
    contexto = buscar_contexto(pergunta, faq)

    if pergunta_pede_dado_sensivel(pergunta):
        return (
            "Eu não preciso de dados pessoais sensíveis para ajudar nos estudos. "
            "Podemos trabalhar apenas com informações gerais, como tempo disponível, objetivo e nível atual. "
            "Próxima ação: diga quantas horas por dia você consegue estudar e qual concurso pretende priorizar.",
            contexto,
        )

    if pergunta_pede_promessa_aprovacao(pergunta):
        return (
            "Não posso garantir aprovação. Nenhum assistente, método ou ferramenta consegue prometer esse resultado com segurança. "
            "Meu papel é ajudar você a organizar rotina, revisão, questões e análise de erros com base na base de conhecimento do projeto. "
            "Próxima ação: defina uma meta de estudo para hoje e registre o que foi feito.",
            contexto,
        )

    if pergunta_pede_dado_atualizado(pergunta) and not contexto:
        return (
            "Não tenho informação suficiente na base para responder com segurança sobre dados oficiais atualizados. "
            "Para edital, banca, salário, vagas, requisitos ou datas, consulte sempre o edital oficial e o site da banca organizadora. "
            "Próxima ação: use o edital oficial como fonte e traga aqui os tópicos que deseja transformar em plano de estudo.",
            contexto,
        )

    if not contexto:
        return (
            "Não encontrei informação suficiente na base de conhecimento para responder com segurança. "
            "Posso ajudar melhor se a dúvida estiver relacionada a rotina de estudos, revisão, questões, simulados ou caderno de erros. "
            "Próxima ação: reformule sua pergunta incluindo seu objetivo e tempo disponível.",
            contexto,
        )

    partes = []
    partes.append("Com base na base de conhecimento do projeto, minha orientação é:")
    for item in contexto:
        partes.append(f"- {item['resposta']}")

    if any(palavra in pergunta.lower() for palavra in ["trilha", "plano", "cronograma", "30 dias"]):
        trilha = trilhas["trilhas"][0]
        partes.append(f"\nSugestão de trilha: **{trilha['nome']}**.")
        partes.append(f"Objetivo: {trilha['objetivo']}")
        partes.append("Próxima ação: escolha uma disciplina prioritária e faça um bloco de teoria curta + 10 questões.")

    elif pergunta_pede_dado_atualizado(pergunta):
        partes.append("\nObservação de segurança: dados oficiais podem mudar. Confirme sempre no edital e na banca organizadora.")

    else:
        partes.append("\nPróxima ação: transforme essa orientação em uma tarefa simples para hoje e registre o resultado.")

    return "\n".join(partes), contexto



def tentar_resposta_com_ollama(pergunta: str, contexto: list[dict]) -> str | None:
    """Gera resposta com LLM local via Ollama, quando configurado.

    O protótipo continua funcionando sem Ollama. Se não houver serviço local,
    a aplicação usa a resposta segura baseada em regras.
    """
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2")

    if not contexto:
        return None

    contexto_texto = "\n".join(
        f"- Pergunta base: {item['pergunta']}\n  Resposta base: {item['resposta']}"
        for item in contexto
    )

    prompt = f"""
{SYSTEM_PROMPT}

Pergunta do usuário:
{pergunta}

Contexto recuperado da base:
{contexto_texto}

Responda com base apenas no contexto acima.
Se a pergunta exigir dado oficial atualizado, recomende consultar o edital oficial.
Inclua uma próxima ação prática.
"""

    try:
        resposta = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2},
            },
            timeout=20,
        )
        resposta.raise_for_status()
        dados = resposta.json()
        return dados.get("response")
    except Exception:
        return None


def main():
    st.set_page_config(
        page_title="Mentor de Estudos IA",
        page_icon="🧠",
        layout="wide",
    )

    faq, trilhas, regras = carregar_base()

    st.title("Mentor de Estudos IA")
    st.caption("Assistente virtual educacional para organização de estudos em concursos de segurança pública.")

    if "mensagens" not in st.session_state:
        st.session_state.mensagens = [
            {
                "role": "assistant",
                "content": (
                    "Olá. Eu sou o Mentor de Estudos IA. Faça uma pergunta sobre rotina, revisão, "
                    "questões, simulados ou caderno de erros para concursos de segurança pública."
                ),
                "contexto": [],
            }
        ]

    with st.sidebar:
        st.header("Sobre o projeto")
        st.write(
            "Protótipo criado para o Lab DIO: Construa Seu Assistente Virtual Com Inteligência Artificial."
        )
        st.markdown("**O assistente ajuda com:**")
        st.markdown("- rotina de estudos\n- questões\n- revisão\n- simulados\n- caderno de erros\n- trilhas iniciais")
        st.markdown("**O assistente não faz:**")
        st.markdown("- não promete aprovação\n- não inventa edital\n- não coleta dados sensíveis")
        usar_llm = st.toggle(
            "Usar LLM local via Ollama",
            value=False,
            help="Opcional. Se o Ollama local não responder, o app usa o modo seguro baseado em regras.",
        )
        if st.button("Limpar conversa"):
            st.session_state.mensagens = []
            st.rerun()
        with st.expander("System prompt"):
            st.code(SYSTEM_PROMPT, language="markdown")
        with st.expander("Regras de segurança"):
            st.markdown(regras)

        st.header("Perguntas de teste")
        exemplos = [
            "Como começo a estudar para concurso policial?",
            "Tenho 2 horas por dia. Como organizar uma rotina?",
            "O que faço quando erro muitas questões?",
            "Você pode garantir minha aprovação?",
            "Qual é o edital oficial mais recente da PRF?",
            "Você precisa do meu CPF para montar um plano?",
        ]
        for exemplo in exemplos:
            if st.button(exemplo, use_container_width=True):
                st.session_state.pergunta_exemplo = exemplo

        st.header("Base carregada")
        st.metric("FAQs", len(faq))
        st.metric("Trilhas", len(trilhas["trilhas"]))

    for mensagem in st.session_state.mensagens:
        with st.chat_message(mensagem["role"]):
            st.markdown(mensagem["content"])
            contexto = mensagem.get("contexto") or []
            if contexto:
                with st.expander("Trechos usados da base de conhecimento"):
                    for item in contexto:
                        st.markdown(f"**{item['id']} — {item['pergunta']}**")
                        st.write(item["resposta"])

    pergunta_exemplo = st.session_state.pop("pergunta_exemplo", None)
    pergunta = pergunta_exemplo or st.chat_input("Digite sua dúvida sobre estudos para concursos...")

    if pergunta:
        st.session_state.mensagens.append({"role": "user", "content": pergunta, "contexto": []})
        with st.chat_message("user"):
            st.markdown(pergunta)

        resposta_segura, contexto = gerar_resposta(pergunta, faq, trilhas)
        resposta_llm = tentar_resposta_com_ollama(pergunta, contexto) if usar_llm else None
        resposta = resposta_llm or resposta_segura

        if usar_llm and resposta_llm:
            resposta += "\n\n_Modo: LLM local via Ollama com contexto recuperado._"
        elif usar_llm and not resposta_llm:
            resposta += "\n\n_Modo: fallback seguro baseado em regras, pois o Ollama local não respondeu._"

        st.session_state.mensagens.append(
            {"role": "assistant", "content": resposta, "contexto": contexto}
        )

        with st.chat_message("assistant"):
            st.markdown(resposta)
            with st.expander("Trechos usados da base de conhecimento"):
                if contexto:
                    for item in contexto:
                        st.markdown(f"**{item['id']} — {item['pergunta']}**")
                        st.write(item["resposta"])
                else:
                    st.write("Nenhum trecho encontrado.")

    with st.expander("Casos de teste e critérios de avaliação"):
        casos = pd.read_csv(DATA_DIR / "casos_teste.csv")
        st.dataframe(casos, use_container_width=True)


if __name__ == "__main__":
    main()
