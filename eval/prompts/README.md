# Versões de prompt

Cada arquivo `.txt` é um prompt de sistema. O nome do arquivo (sem extensão) é a **versão** registrada no banco.

| Versão | Objetivo |
|---|---|
| `v1` | Prompt de referência: resposta correta, direta e curta. |
| `v2_piorado` | Prompt **piorado de propósito** para demonstrar que a plataforma acusa regressão (critério do Tema 3). |

Para criar uma nova versão, adicione `vN.txt` e rode `python -m src.cli rodar --versao vN`.
