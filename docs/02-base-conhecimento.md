# 02 — Base de Conhecimento

A base de conhecimento do projeto está localizada na pasta `data/`.

## Arquivos

| Arquivo | Tipo | Finalidade |
|---|---|---|
| `faq_estudos.json` | JSON | Perguntas e respostas sobre estudos |
| `trilhas_estudo.json` | JSON | Trilhas mockadas para organização inicial |
| `regras_seguranca.md` | Markdown | Regras de comportamento seguro do agente |
| `casos_teste.csv` | CSV | Perguntas usadas para avaliação |

## Estratégia

A base foi criada com dados fictícios e seguros. Ela evita:

- dados pessoais reais;
- dados sensíveis;
- editais reais atualizados;
- informações que poderiam ficar desatualizadas rapidamente.

## Por que usar dados mockados?

Dados mockados ajudam a demonstrar o conceito de agente com base de conhecimento sem expor pessoas reais ou depender de informações oficiais que mudam com frequência.

## Expansões futuras

- adicionar conteúdos por disciplina;
- adicionar mapa de assuntos por banca;
- incluir níveis de dificuldade;
- usar embeddings para busca semântica;
- integrar banco vetorial.
