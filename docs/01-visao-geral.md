# 1. Visão geral e arquitetura

## Problema

Trocar o prompt de sistema ou o modelo de um assistente pode piorar as respostas sem que ninguém perceba. Avaliar à mão a cada mudança não escala. Usar um LLM para avaliar outro LLM resolve a escala, mas só é confiável se soubermos **quanto o juiz concorda com pessoas** e **em que casos ele erra**.

A plataforma responde a três perguntas:

1. Qual a taxa de acerto de cada modelo em cada versão de prompt?
2. O LLM juiz concorda com avaliadores humanos? (acordo percentual e kappa de Cohen)
3. Uma nova versão piorou o resultado em relação à anterior? (detecção de regressão)

## Diagrama de componentes

```mermaid
flowchart LR
    C[eval/casos.json<br/>100 casos] --> R[runner<br/>fase 1: respostas]
    P[eval/prompts/vN.txt] --> R
    R -->|Ollama| M[(gemma3:4b<br/>llama3.2:3b<br/>qwen2.5:3b)]
    R --> B[baseline<br/>palavra-chave]
    R --> J[juiz LLM<br/>fase 2: qwen2.5:7b]
    B --> DB[(SQLite<br/>eval/avaliacoes.db)]
    J --> DB
    H[avaliação humana<br/>painel] --> DB
    DB --> CLI[CLI: comparar, concordancia,<br/>exportar, erros]
    DB --> UI[Painel Streamlit]
    CLI --> E[evidencias/erros/*.png<br/>eval/resultados/]
```

## Fluxo de dados de uma bateria

```mermaid
sequenceDiagram
    participant U as Usuário (CLI)
    participant R as runner.py
    participant O as Ollama
    participant S as SQLite
    U->>R: rodar --versao v1
    R->>S: cria execução (modelo, versão, juiz, split)
    loop Fase 1: para cada caso
        R->>O: pergunta + prompt de sistema (modelo avaliado)
        O-->>R: resposta, tempo, tokens
        R->>R: baseline (palavra-chave)
        R->>S: grava resultado
    end
    R->>O: descarrega o modelo avaliado (keep_alive=0)
    loop Fase 2: para cada resposta
        R->>O: pergunta + referência + resposta (juiz, formato JSON)
        O-->>R: {"aprovado", "justificativa"}
        R->>S: grava veredito do juiz
    end
    U->>S: notas humanas (painel ou importar-humano)
    U->>S: comparar / concordancia / exportar / erros
```

1. **Entrada:** os casos de teste ([eval/casos.json](../eval/casos.json)) e uma versão de prompt ([eval/prompts/](../eval/prompts/)).
2. **Fase 1 (respostas):** cada modelo avaliado responde a todos os casos com temperatura 0 e seed fixa. O baseline avalia cada resposta na hora.
3. **Fase 2 (juiz):** o modelo avaliado é descarregado da memória e o juiz avalia todas as respostas.
4. **Avaliação humana:** integrantes do grupo dão notas no painel sem ver os vereditos automáticos.
5. **Saída:** métricas, regressão e concordância na CLI e no painel; CSV, `metricas.json`, logs e imagens dos erros como evidência.

## Módulos

| Módulo | Responsabilidade |
|---|---|
| [src/casos.py](../src/casos.py) | Carrega e valida os casos e as versões de prompt |
| [src/model_runner.py](../src/model_runner.py) | Chamada aos modelos via Ollama (temperatura 0, seed 42), medição de tempo e tokens |
| [src/baseline.py](../src/baseline.py) | Aprova a resposta se ela contém uma palavra-chave esperada |
| [src/judge.py](../src/judge.py) | LLM juiz: prompt versionado e interpretação do veredito em JSON |
| [src/runner.py](../src/runner.py) | Bateria em duas fases, com logs datados |
| [src/evaluation.py](../src/evaluation.py) | Taxa de acerto, kappa de Cohen, matriz de confusão e regressão |
| [src/results_store.py](../src/results_store.py) | Persistência em SQLite, com migração de bancos antigos |
| [src/erros.py](../src/erros.py) | Classificação dos casos de falha e geração de imagens |
| [src/cli.py](../src/cli.py) | Linha de comando |
| [src/app.py](../src/app.py) | Painel Streamlit |

## Modelo de dados

O banco SQLite tem duas tabelas.

```mermaid
erDiagram
    execucoes ||--o{ resultados : contem
    execucoes {
        int id PK
        text data_hora
        text descricao
        text origem "bateria ou manual"
        text modelo
        text versao_prompt
        text prompt_sistema
        text modelo_juiz
        text versao_prompt_juiz
        text arquivo_casos
        text split
    }
    resultados {
        int id PK
        int execucao_id FK
        text caso_id
        text categoria
        text pergunta
        text resposta_referencia
        text resposta
        int aprovado_baseline
        int aprovado_juiz
        text justificativa_juiz
        int aprovado_humano
        text avaliador_humano
        real tempo_resposta
        int tokens_entrada
        int tokens_saida
        real tempo_juiz
        int tokens_juiz
        text erro
    }
```

Cada execução guarda a versão e o texto do prompt, o modelo juiz e a versão do prompt do juiz. Assim, qualquer resultado pode ser rastreado até a configuração que o produziu. Ao iniciar, `initialize_database` cria as tabelas e acrescenta colunas que faltem em bancos de versões anteriores.
