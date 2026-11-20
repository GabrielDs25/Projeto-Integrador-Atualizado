# Casos de falha

Imagens geradas automaticamente a partir dos resultados gravados no banco
(`python -m src.cli erros <execuções>`). Cada imagem informa no rodapé a
execução e o resultado de origem. A coluna **Causa provável** é preenchida
pelo grupo após analisar cada caso (exigência da evidência 6).

| Tipo | Quantidade |
|---|---|
| Falha de execução tratada | 0 |
| Modelo respondeu errado | 3 |
| Juiz divergiu do humano | 0 |
| Baseline divergiu do humano | 0 |
| Juiz e baseline divergem: avaliar à mão | 6 |

| Imagem | Execução | Caso | Modelo | Prompt | Tipos | Resposta do modelo | Causa provável |
|---|---|---|---|---|---|---|---|
| [erro_exec3_C004_modelo_errou.png](erro_exec3_C004_modelo_errou.png) | 3 | C004 | llama3.2:3b | v2_piorado | Modelo respondeu errado | Isso envolve uma operação matemática básica. Em Python, você pode obt… | _a preencher_ |
| [erro_exec3_C005_modelo_errou.png](erro_exec3_C005_modelo_errou.png) | 3 | C005 | llama3.2:3b | v2_piorado | Modelo respondeu errado | Uma função em Python é definida por uma palavra-chave específica. | _a preencher_ |
| [erro_exec3_C006_revisar.png](erro_exec3_C006_revisar.png) | 3 | C006 | llama3.2:3b | v2_piorado | Juiz e baseline divergem: avaliar à mão | Em Python, o valor 3.14 é considerado um número real. | _a preencher_ |
| [erro_exec3_C007_modelo_errou.png](erro_exec3_C007_modelo_errou.png) | 3 | C007 | llama3.2:3b | v2_piorado | Modelo respondeu errado | Em Python, a função len() é usada para obter o número de elementos em… | _a preencher_ |
| [erro_exec3_C008_revisar.png](erro_exec3_C008_revisar.png) | 3 | C008 | llama3.2:3b | v2_piorado | Juiz e baseline divergem: avaliar à mão | Existem vários métodos que podem ser usados para adicionar um element… | _a preencher_ |
| [erro_exec2_C004_revisar.png](erro_exec2_C004_revisar.png) | 2 | C004 | llama3.2:3b | v2_piorado | Juiz e baseline divergem: avaliar à mão | Isso envolve uma operação matemática básica. Em Python, você pode obt… | _a preencher_ |
| [erro_exec2_C005_revisar.png](erro_exec2_C005_revisar.png) | 2 | C005 | llama3.2:3b | v2_piorado | Juiz e baseline divergem: avaliar à mão | Uma função em Python é definida por uma palavra-chave específica. | _a preencher_ |
| [erro_exec2_C006_revisar.png](erro_exec2_C006_revisar.png) | 2 | C006 | llama3.2:3b | v2_piorado | Juiz e baseline divergem: avaliar à mão | Em Python, o valor 3.14 é considerado um número real. | _a preencher_ |
| [erro_exec2_C007_revisar.png](erro_exec2_C007_revisar.png) | 2 | C007 | llama3.2:3b | v2_piorado | Juiz e baseline divergem: avaliar à mão | Em Python, a função len() é usada para obter o número de elementos em… | _a preencher_ |
