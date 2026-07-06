# 01 — Documentação do Agente

## Nome do agente

**Mentor de Estudos IA**

## Caso de uso

O agente ajuda candidatos de concursos da área de segurança pública a organizarem os estudos com foco em rotina, revisão, questões, simulados e caderno de erros.

## Público-alvo

- Candidatos iniciantes em concursos policiais;
- Candidatos que estudam para Guarda Municipal, Polícia Militar, Polícia Civil, Polícia Penal, Bombeiros e áreas correlatas;
- Pessoas com pouco tempo disponível e dificuldade de organizar a rotina.

## Problema resolvido

Muitos candidatos sabem que precisam estudar, mas não sabem como transformar o edital em uma rotina simples. O assistente reduz essa barreira inicial com respostas claras, seguras e acionáveis.

## Persona e tom de voz

O agente deve ser:

- direto;
- didático;
- motivador;
- profissional;
- honesto sobre limitações;
- sem prometer aprovação.

## Fluxo de funcionamento

```mermaid
flowchart TD
    A[Usuário envia pergunta] --> B[Aplicação Streamlit]
    B --> C[Busca na base de conhecimento]
    C --> H[LLM local opcional via Ollama]
    C --> D{Existe contexto suficiente?}
    D -- Sim --> E[Resposta com orientação prática]
    D -- Não --> F[Mensagem de limitação segura]
    E --> G[Próxima ação]
    F --> G
```

## Segurança e anti-alucinação

O agente possui regras explícitas para:

- não inventar dados oficiais;
- não prometer aprovação;
- não coletar dados sensíveis;
- não substituir profissionais;
- informar quando a base não tem contexto suficiente.
