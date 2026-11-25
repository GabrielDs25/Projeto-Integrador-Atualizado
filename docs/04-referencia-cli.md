# 4. Referência da CLI e do painel

A plataforma não expõe API HTTP. A interação é feita pela **linha de comando** (`python -m src.cli`) e pelo **painel Streamlit** (`src/app.py`). Todos os comandos são executados a partir da raiz do repositório.

```bash
python -m src.cli --help
python -m src.cli <comando> --help
```

## Códigos de saída

| Código | Significado |
|---|---|
| 0 | Sucesso |
| 1 | `comparar` detectou regressão. É o código que faz um pipeline de CI falhar. |
| 2 | Erro de uso: execução inexistente, modelo não instalado, arquivo ou versão de prompt não encontrados, Ollama inacessível |

## `rodar`

Roda a bateria de casos em cada modelo e cria uma execução por modelo.

```bash
python -m src.cli rodar --versao v1
python -m src.cli rodar --versao v2_piorado --modelos gemma3:4b --limite 10
```

| Opção | Padrão | Descrição |
|---|---|---|
| `--versao` | `v1` | Versão do prompt de sistema (arquivo `eval/prompts/<versao>.txt`) |
| `--modelos` | `MODELOS_AVALIADOS` | Modelos separados por vírgula |
| `--casos` | `eval/casos.json` | Arquivo de casos |
| `--split` | `teste` | `teste`, `calibracao` ou `todos` |
| `--limite N` | todos | Roda só os N primeiros casos (para testes rápidos) |
| `--juiz` | `MODELO_JUIZ` | Modelo juiz |
| `--sem-juiz` | desligado | Avalia só com o baseline |
| `--descricao` | vazio | Texto livre gravado na execução |

Antes de começar, confere se todos os modelos estão instalados. Grava o log em `eval/logs/bateria-<data>-<versao>.log` e, ao final, imprime a taxa de acerto do juiz e do baseline, o tempo total e os tokens de cada execução.

## `execucoes`

Lista as baterias com data, modelo, versão do prompt, número de casos e taxas de acerto (juiz, baseline e humano).

| Opção | Descrição |
|---|---|
| `--todas` | Inclui as perguntas avulsas feitas no painel |

## `comparar BASE NOVA`

Compara duas execuções e acusa regressão se a taxa de acerto cair mais que o limiar. Lista os casos que passavam na base e falham na nova versão.

```bash
python -m src.cli comparar 4 5 --limiar 5
```

| Opção | Padrão | Descrição |
|---|---|---|
| `--limiar` | `5.0` | Queda máxima aceita, em pontos percentuais |
| `--campo` | `juiz` | Avaliador usado na comparação: `juiz`, `baseline` ou `humano` |

Sai com código **1** quando há regressão e **0** quando não há.

## `concordancia ID [ID ...]`

Calcula, para o juiz e para o baseline em relação às notas humanas: número de pares, acordo percentual, kappa de Cohen (com a interpretação de Landis e Koch) e matriz de confusão.

| Opção | Descrição |
|---|---|
| `--detalhes` | Lista cada divergência, com a resposta e a justificativa do juiz |

## `exportar ID [ID ...]`

Gera `execucao_<id>.csv` para cada execução e um `metricas.json` com as métricas e a concordância.

| Opção | Padrão |
|---|---|
| `--saida` | `eval/resultados/` |

## `erros [ID ...]`

Classifica os casos de falha e gera uma imagem PNG para cada um, além do índice `README.md` e de `erros.json`. Sem IDs, usa todas as baterias. A coluna "Causa provável" preenchida à mão no índice é preservada quando o comando roda de novo.

| Tipo | Quando ocorre |
|---|---|
| `falha_execucao` | O modelo ou o juiz falhou (fora do ar, formato inválido) e o sistema registrou o erro |
| `modelo_errou` | O humano reprovou a resposta. Sem nota humana: juiz e baseline reprovaram. |
| `juiz_errou` | O veredito do juiz diverge da nota humana |
| `baseline_errou` | O veredito do baseline diverge da nota humana |
| `revisar` | Sem nota humana, juiz e baseline discordam |

| Opção | Padrão | Descrição |
|---|---|---|
| `--saida` | `evidencias/erros/` | Pasta de destino |
| `--tipo` | todos | Filtra por tipo (pode ser repetido) |

## `importar-humano ARQUIVO --avaliador NOME`

Importa notas humanas de um CSV no formato gerado por `exportar`, preenchido na coluna `aprovado_humano` com `sim`/`não`, `true`/`false` ou `1`/`0`. Linhas vazias são ignoradas. Serve para avaliar em planilha em vez de usar o painel.

## Painel Streamlit

```bash
python -m streamlit run src/app.py   # http://localhost:8501
```

| Visão | Função |
|---|---|
| Resultados por versão | Gráfico de acerto por modelo e versão, tabela de execuções e detalhes de cada resposta |
| Regressão | Escolha da execução base, da nova e do limiar, com o resultado da comparação |
| Avaliação humana | Tabela editável para dar nota às respostas sem ver os vereditos automáticos |
| Juiz × humano | Acordo, kappa e matriz de confusão do juiz e do baseline, e lista dos casos em que o juiz errou |
| Pergunta livre | Pergunta avulsa a vários modelos. Não entra nas métricas das baterias. |

O passo a passo está no [Manual do usuário](09-manual-usuario.md).
