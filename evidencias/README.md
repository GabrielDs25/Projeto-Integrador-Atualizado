# Índice de evidências

Liga cada afirmação do trabalho de pesquisa à evidência que a comprova (evidência 8 do enunciado).

| # | Evidência | Onde está | Como regerar |
|---|---|---|---|
| 1 | Vídeo da execução (3 a 5 min) | _(link ou arquivo)_ | — |
| 2 | Execução verde da CI na tag v1.0 | _(link da execução)_ + `ci-verde.png` | — |
| 3 | Resultados da avaliação | [../eval/resultados/](../eval/resultados/) | `python -m src.cli exportar <ids>` |
| 4 | Logs de uma execução completa | [../eval/logs/](../eval/logs/) | `python -m src.cli rodar --versao v1` |
| 5 | Capturas de tela do painel | [capturas/](capturas/) | — |
| 6 | Casos de falha com análise | [erros/](erros/) | `python -m src.cli erros <ids>` |
| 7 | Histórico do Git e PRs revisados | _(link do repositório)_ | — |

## Afirmações do trabalho e evidências

| Afirmação no trabalho | Evidência |
|---|---|
| _(ex.: "o juiz teve kappa X contra notas humanas")_ | `eval/resultados/metricas.json`, seção concordancia |
| _(ex.: "a plataforma acusou a regressão do prompt v2_piorado")_ | saída de `comparar`, captura `capturas/regressao.png` |
