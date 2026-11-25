# Documentação técnica: Plataforma de avaliação de LLMs

Esta documentação permite que uma pessoa que não participou do projeto instale, use e reproduza os resultados da plataforma. O trabalho de pesquisa (padrão ABNT) fica em [pesquisa-abnt.pdf](pesquisa-abnt.pdf).

A plataforma funciona como uma "integração contínua para IA": roda uma bateria de perguntas de programação sobre modelos de linguagem locais e versões de prompt, avalia as respostas com um **LLM juiz** e com um **baseline por palavra-chave**, mede quanto o juiz concorda com **notas humanas** e **acusa regressão** quando uma nova versão piora o resultado.

## Sumário

| # | Seção | Conteúdo |
|---|---|---|
| 1 | [Visão geral e arquitetura](01-visao-geral.md) | Componentes, fluxo de dados e modelo de dados |
| 2 | [Instalação e execução](02-instalacao.md) | Pré-requisitos, Docker, execução local e variáveis de ambiente |
| 3 | [Decisões de arquitetura](03-decisoes.md) | Cinco registros com contexto, decisão e alternativas descartadas |
| 4 | [Referência da CLI e do painel](04-referencia-cli.md) | Todos os comandos, opções e códigos de saída |
| 5 | [Dados e modelos](05-dados-e-modelos.md) | Conjunto de casos, fichas dos modelos e licenças |
| 6 | [Guia de avaliação](06-guia-avaliacao.md) | Como reproduzir os experimentos e as métricas |
| 7 | [Testes e integração contínua](07-testes-ci.md) | O que é testado, como rodar e cobertura |
| 8 | [Segurança, privacidade e limitações](08-seguranca-limitacoes.md) | Riscos, o que o sistema não faz e LGPD |
| 9 | [Manual do usuário](09-manual-usuario.md) | Passo a passo no painel, com capturas de tela |

## Início rápido

```bash
git clone https://github.com/GabrielDs25/Projeto-Integrador-Atualizado.git
cd Projeto-Integrador-Atualizado
docker compose up
```

Abra http://localhost:8501. Detalhes em [Instalação e execução](02-instalacao.md).
