# 7. Testes e integração contínua

## Como executar

```bash
pip install -r requirements-dev.txt
pytest                 # 50 testes
pytest --cov           # com cobertura
ruff check .           # lint
```

Os testes **não precisam do Ollama nem de modelos**. O arquivo [tests/conftest.py](../tests/conftest.py) define um `ClienteFalso` que imita o `ollama.Client`: devolve respostas programadas por modelo, pode simular um modelo fora do ar e conta as chamadas. Cada teste usa um banco SQLite temporário.

## O que é testado

| Arquivo | O que verifica |
|---|---|
| [test_baseline.py](../tests/test_baseline.py) | Normalização de acentos e maiúsculas, palavra-chave como termo inteiro, resposta vazia, limitação conhecida com negação |
| [test_casos.py](../tests/test_casos.py) | 100 casos únicos com divisão 30/70, baseline aprova a própria referência, validação de ID repetido e campo faltando, existência dos prompts |
| [test_model_runner.py](../tests/test_model_runner.py) | Modelos configurados por variável, bloqueio de modelo não permitido, medição de tokens, Ollama fora do ar |
| [test_judge.py](../tests/test_judge.py) | Interpretação de JSON válido, cercado de texto, malformado e inválido, uso de formato JSON na chamada |
| [test_runner.py](../tests/test_runner.py) | Bateria completa nas duas fases, falha do modelo e do juiz registradas sem derrubar a bateria, execução sem juiz |
| [test_evaluation.py](../tests/test_evaluation.py) | Taxa de acerto, kappa com exemplo calculado à mão e casos-limite, matriz de confusão, regressão dentro e fora do limiar |
| [test_results_store.py](../tests/test_results_store.py) | Gravação e leitura, avaliação humana, chave estrangeira, migração de banco antigo |
| [test_erros.py](../tests/test_erros.py) | Classificação dos tipos de erro, filtro por tipo, geração das imagens e preservação das causas preenchidas à mão |
| [test_cli.py](../tests/test_cli.py) | `comparar` sai com 1 em regressão e 0 sem regressão, execução inexistente, ciclo exportar → importar notas humanas → concordância |

## Cobertura

Medida com `pytest --cov` em 25/11/2026:

| Módulo | Cobertura |
|---|---|
| `baseline.py` | 100% |
| `evaluation.py` | 98% |
| `results_store.py` | 97% |
| `erros.py` | 97% |
| `runner.py` | 96% |
| `model_runner.py` | 93% |
| `casos.py` | 92% |
| `judge.py` | 92% |
| `cli.py` | 64% |
| **Total** | **86%** |

O painel (`src/app.py`) fica fora da medição (configurado em `pyproject.toml`), porque é interface e é verificado manualmente. Na CLI, os trechos não cobertos são os comandos que dependem de modelos reais (`rodar`) e a formatação de saída.

## Integração contínua

O workflow [.github/workflows/ci.yml](../.github/workflows/ci.yml) roda no GitHub Actions a cada push na `main`, a cada tag `v*` e em todo pull request:

1. Instala o Python 3.12 e as dependências de `requirements-dev.txt`.
2. Roda o lint (`ruff check .`).
3. Roda os testes com cobertura (`pytest --cov`).
4. Guarda o relatório `coverage.xml` como artefato da execução.

Se o lint ou algum teste falhar, a execução fica vermelha e o pull request mostra a falha.

### Usar a detecção de regressão como etapa de CI

O comando `comparar` sai com código 1 quando há regressão, então pode bloquear um pipeline. Como as baterias exigem modelos (horas em CPU), essa etapa não roda no GitHub Actions. O uso previsto é em uma máquina com Ollama:

```bash
python -m src.cli rodar --versao vNOVA --modelos gemma3:4b
python -m src.cli comparar <id_base> <id_novo> || echo "Regressão: não publicar a nova versão do prompt"
```
