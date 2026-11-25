# 6. Guia de avaliação

Como reproduzir os experimentos e calcular as métricas.

## Protocolo

1. **Conjunto de teste separado:** os experimentos usam os 70 casos de `teste`. Os 30 de `calibracao` servem apenas para ajustar o prompt do juiz.
2. **Baseline:** comparação por palavra-chave, calculada para toda resposta.
3. **Juiz:** `qwen2.5:7b` com o prompt `juiz-v1`.
4. **Referência humana:** no mínimo 30 respostas avaliadas por integrantes do grupo, sem ver o veredito do juiz nem o do baseline.
5. **Regressão:** a versão `v2_piorado` é pior de propósito. O comando `comparar` precisa acusar a queda.
6. **Custo:** tempo e tokens de cada resposta e de cada veredito são registrados.

## Reproduzir passo a passo

```bash
# 1. Bateria de referência (70 casos x 3 modelos)
python -m src.cli rodar --versao v1 --descricao "oficial v1"

# 2. Bateria com o prompt piorado
python -m src.cli rodar --versao v2_piorado --descricao "oficial v2_piorado"

# 3. Ver os IDs das execuções
python -m src.cli execucoes

# 4. Regressão: para cada modelo, compare a execução v1 com a v2_piorado do mesmo modelo
python -m src.cli comparar <id_v1> <id_v2_piorado>

# 5. Avaliação humana no painel (visão "Avaliação humana"), no mínimo 30 respostas

# 6. Concordância do juiz e do baseline com as notas humanas
python -m src.cli concordancia <ids...> --detalhes

# 7. Evidências
python -m src.cli exportar <ids...>     # eval/resultados/*.csv e metricas.json
python -m src.cli erros <ids...>        # evidencias/erros/*.png
```

Para uma rodada rápida, acrescente `--limite 5` ao comando `rodar`. Para ajustar o juiz, use `--split calibracao`.

A bateria completa leva horas em CPU. Por isso cada resposta é gravada no banco assim que gerada e o log mostra o progresso em `eval/logs/`.

## Métricas

| Métrica | Definição | Onde |
|---|---|---|
| Taxa de acerto | Aprovados ÷ avaliados × 100, calculada separadamente para juiz, baseline e humano. Casos sem nota não entram no denominador. | `evaluation.accuracy_rate` |
| Acordo percentual | Casos em que o avaliador e o humano deram a mesma nota ÷ casos avaliados pelos dois | `evaluation.concordancia` |
| Kappa de Cohen | κ = (pₒ − pₑ) ÷ (1 − pₑ), em que pₒ é o acordo observado e pₑ o acordo esperado ao acaso | `evaluation.cohen_kappa` |
| Matriz de confusão | Verdadeiro/falso positivo e negativo, com o humano como verdade. Falso positivo = o avaliador aprovou o que o humano reprovou. | `evaluation.concordancia` |
| Regressão | Δ = taxa nova − taxa base. Há regressão se Δ < −limiar (padrão: 5 pontos percentuais). Também lista os casos que passavam e passaram a falhar. | `evaluation.detectar_regressao` |
| Custo | Tempo médio e total (resposta + juiz) e tokens totais (entrada + saída + juiz) | `evaluation.calculate_metrics` |

### Interpretação do kappa (Landis e Koch, 1977)

| κ | Concordância |
|---|---|
| < 0 | Pior que o acaso |
| 0,00 a 0,20 | Leve |
| 0,21 a 0,40 | Razoável |
| 0,41 a 0,60 | Moderada |
| 0,61 a 0,80 | Substancial |
| 0,81 a 1,00 | Quase perfeita |

O kappa é mais informativo que o acordo percentual quando quase todas as respostas são aprovadas: nesse caso, um avaliador que aprova tudo teria acordo alto, mas kappa próximo de zero.

## Saídas geradas

| Arquivo | Conteúdo |
|---|---|
| `eval/avaliacoes.db` | Banco com todas as execuções e resultados (não versionado) |
| `eval/logs/bateria-<data>-<versao>.log` | Log datado de cada bateria: pergunta, resposta, tempo, vereditos e justificativas |
| `eval/resultados/execucao_<id>.csv` | Todas as respostas de uma execução |
| `eval/resultados/metricas.json` | Métricas por execução e concordância juiz × humano e baseline × humano |
| `evidencias/erros/*.png`, `README.md`, `erros.json` | Imagens e índice dos casos de falha, com a coluna "Causa provável" para análise |

## Reprodutibilidade

- Temperatura 0 e seed fixa em todas as chamadas.
- Divisão fixa entre calibração e teste.
- Versão do prompt, texto do prompt, modelo juiz e versão do prompt do juiz gravados em cada execução.
- Dependências Python com versões fixas em `requirements.txt`.

Mesmo assim, respostas podem variar ligeiramente entre máquinas (CPU ou GPU, versão do Ollama, quantização do modelo). As conclusões devem se apoiar nas taxas agregadas, não em respostas individuais.
