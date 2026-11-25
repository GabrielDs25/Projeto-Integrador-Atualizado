# 5. Dados e modelos

## Conjunto de casos de teste

### Ficha do conjunto de dados

| Item | Descrição |
|---|---|
| Arquivo | [eval/casos.json](../eval/casos.json) |
| Origem | Elaborado pelo grupo para este projeto. As perguntas, respostas de referência e palavras-chave estão escritas em [eval/gerar_casos.py](../eval/gerar_casos.py), que gera o JSON. Não foram usados dados de terceiros. |
| Tamanho | 100 perguntas curtas de programação, em português |
| Divisão | 30 de **calibração** e 70 de **teste**, fixa e determinística: em cada bloco de 10 casos, os 3 primeiros são de calibração |
| Licença | _(a definir pelo grupo: o repositório ainda não tem arquivo LICENSE)_ |
| Dados pessoais | Nenhum |
| Finalidade | Medir se modelos pequenos respondem corretamente a perguntas factuais de programação e calibrar o LLM juiz |
| Fora do escopo | Perguntas abertas, geração de código longo, raciocínio em várias etapas, outros idiomas |

### Categorias

| Categoria | Casos |
|---|---|
| `python` | 30 |
| `algoritmos` | 20 |
| `web` | 15 |
| `devops` | 15 |
| `banco_dados` | 10 |
| `ia` | 10 |
| **Total** | **100** |

### Formato de um caso

```json
{
  "id": "C004",
  "split": "teste",
  "categoria": "python",
  "pergunta": "Qual o resultado de 7 % 3 em Python?",
  "resposta_referencia": "1",
  "palavras_chave": ["1", "um"]
}
```

| Campo | Uso |
|---|---|
| `id` | Identificador único (`C001` a `C100`) |
| `split` | `calibracao` ou `teste` |
| `pergunta` | Texto enviado ao modelo avaliado |
| `resposta_referencia` | Resposta correta, mostrada ao juiz e ao avaliador humano |
| `palavras_chave` | Termos que o baseline aceita como resposta correta |

### Tratamento

- [src/casos.py](../src/casos.py) valida o arquivo ao carregá-lo: campos obrigatórios, `split` válido, IDs únicos e `palavras_chave` como lista. Qualquer problema interrompe a execução com uma mensagem clara.
- Um teste automatizado garante que existem 100 casos únicos, que a divisão é 30/70 e que o baseline aprova a própria resposta de referência de cada caso.
- Para alterar os casos, edite `eval/gerar_casos.py` e rode `python eval/gerar_casos.py`. Não edite o JSON à mão.

## Versões de prompt

| Versão | Arquivo | Objetivo |
|---|---|---|
| `v1` | [eval/prompts/v1.txt](../eval/prompts/v1.txt) | Prompt de referência: resposta correta, direta, em até duas frases |
| `v2_piorado` | [eval/prompts/v2_piorado.txt](../eval/prompts/v2_piorado.txt) | Piorado de propósito (respostas vagas) para demonstrar a detecção de regressão |
| `juiz-v1` | [src/judge.py](../src/judge.py) | Prompt do LLM juiz (aprovado/reprovado com justificativa, em JSON) |

O texto completo do prompt de sistema e a versão do prompt do juiz ficam gravados em cada execução.

## Modelos

Todos são executados localmente via Ollama, com `temperature=0` e `seed=42`. O juiz usa janela de contexto de 2048 tokens e saída em formato JSON.

| Modelo | Papel | Parâmetros | Desenvolvedor | Licença |
|---|---|---|---|---|
| `gemma3:4b` | Avaliado | 4 bilhões | Google | Gemma Terms of Use |
| `llama3.2:3b` | Avaliado | 3 bilhões | Meta | Llama 3.2 Community License |
| `qwen2.5:3b` | Avaliado | 3 bilhões | Alibaba (Qwen) | Qwen Research License |
| `qwen2.5:7b` | Juiz | 7 bilhões | Alibaba (Qwen) | Apache 2.0 |

### Ficha do modelo juiz

| Item | Descrição |
|---|---|
| Modelo | `qwen2.5:7b` via Ollama (quantização padrão da biblioteca Ollama) |
| Tarefa | Decidir se a resposta de um modelo traz a informação da resposta de referência |
| Entrada | Pergunta, resposta de referência e resposta do modelo |
| Saída | `{"aprovado": true/false, "justificativa": "..."}` |
| Critério | Aceita sinônimos, outro idioma, formatação diferente e explicações extras que não contradigam a referência. Reprova respostas erradas, vagas, evasivas ou contraditórias. |
| Falhas tratadas | Texto fora do JSON é recuperado por expressão regular. Se não for possível interpretar, o veredito fica vazio e o erro `ERRO_FORMATO` é registrado. |
| Validação | Concordância com notas humanas (acordo percentual e kappa de Cohen). Ver o [Guia de avaliação](06-guia-avaliacao.md). |
| Limitações conhecidas | Pode aceitar respostas parcialmente corretas, depende da qualidade da resposta de referência e é da mesma família de um dos modelos avaliados (`qwen2.5:3b`) |

Antes de redistribuir resultados ou usar os modelos fora do contexto acadêmico, consulte o cartão de cada modelo na biblioteca do Ollama e a licença do desenvolvedor.

## Licenças das dependências

Ollama (MIT), Streamlit (Apache 2.0), pandas (BSD-3), Pillow (MIT-CMU), pytest (MIT), pytest-cov (MIT), Ruff (MIT).
