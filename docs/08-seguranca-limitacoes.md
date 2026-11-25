# 8. Segurança, privacidade e limitações

## Segurança

| Aspecto | Situação |
|---|---|
| Segredos | Não há chaves de API nem senhas. O `.env` está no `.gitignore` e o `.env.example` só traz valores padrão. |
| Tráfego externo | Perguntas e respostas não saem da máquina: os modelos rodam no Ollama local. A internet só é usada para baixar modelos e dependências. |
| Exposição de rede | No Docker, apenas a porta 8501 (painel) é publicada. O Ollama fica acessível só na rede interna do Compose. O painel **não tem autenticação**: não deve ser exposto na internet. |
| SQL | Todas as consultas com valores do usuário usam parâmetros (`?`). Nomes de colunas vêm de listas fixas no código. |
| Modelos permitidos | `gerar_resposta` recusa modelos fora da lista configurada. |
| Falhas | Erro de um modelo ou do juiz é registrado no resultado (campo `erro`) e a bateria continua. Veredito em formato inválido vira `ERRO_FORMATO`, nunca uma aprovação. |
| Dependências | Versões fixas em `requirements.txt`. A imagem `ollama/ollama:latest` não tem versão fixa e pode mudar entre instalações. |

## Privacidade e LGPD

| Dado | Tratamento |
|---|---|
| Casos de teste | Perguntas técnicas, sem dados pessoais |
| Nome do avaliador humano | Único dado pessoal armazenado (coluna `avaliador_humano`). Finalidade: rastrear quem deu cada nota. É tratado apenas localmente, no banco SQLite. |
| Pergunta livre do painel | Texto digitado pelo usuário, gravado no banco. Não deve conter dados pessoais ou sigilosos. |
| Banco de dados | Fica só na máquina de quem roda o sistema. `*.db` está no `.gitignore` e não vai para o repositório. |
| Logs e evidências | Contêm perguntas e respostas dos modelos, sem dados pessoais. O CSV exportado inclui o nome do avaliador, que pode ser removido antes de publicar. |

Em conformidade com a LGPD (Lei nº 13.709/2018): coletamos só o mínimo necessário (o nome do avaliador), para uma finalidade definida (rastreabilidade da avaliação), sem compartilhar com terceiros nem enviar para fora da máquina. Para excluir os dados de um avaliador, basta limpar a coluna `avaliador_humano` no banco ou apagar o arquivo `eval/avaliacoes.db`.

## O que o sistema não faz

- Não avalia código longo, nem respostas abertas ou subjetivas. Os casos são perguntas factuais com resposta curta.
- Não executa o código das respostas: a avaliação é textual.
- Não substitui a avaliação humana. O juiz só é confiável na medida da concordância medida com as notas humanas.
- Não compara modelos comerciais via API.
- Não suporta vários usuários simultâneos nem tem controle de acesso.
- Não roda baterias reais no GitHub Actions: a CI testa o código com um cliente falso.

## Limitações conhecidas

| Limitação | Efeito |
|---|---|
| Baseline ingênuo | Aprova "não é 8" quando a palavra-chave é "8" (negação) e reprova sinônimos fora da lista. Há um teste que documenta esse comportamento. |
| Vieses do juiz | Pode aprovar respostas parcialmente corretas ou longas e depende da qualidade da resposta de referência. É da mesma família de um modelo avaliado (`qwen2.5:3b`). |
| Tamanho do conjunto | 70 casos de teste, todos em português e em temas de programação. Taxas de acerto têm margem de erro de alguns pontos percentuais. |
| Escopo dos modelos | Modelos de 3 a 7 bilhões de parâmetros. As conclusões não se estendem a modelos maiores. |
| Custo de tempo | Em CPU, uma bateria completa de um modelo leva algumas horas, a maior parte no juiz. |
| Reprodutibilidade | Temperatura 0 e seed fixa reduzem a variação, mas respostas podem mudar entre hardware, versões do Ollama e quantizações. |
| Interrupção | Se a máquina hibernar ou a bateria for interrompida na fase do juiz, alguns resultados ficam sem veredito. Eles são ignorados no cálculo da taxa, então a execução deve ser refeita se faltarem muitos. |

## Riscos éticos

- **Confiança excessiva no juiz:** usar a taxa do juiz como verdade sem olhar a concordância com pessoas pode esconder erros sistemáticos. Por isso o painel mostra a concordância e os casos em que o juiz errou.
- **Viés de avaliação humana:** quem avalia pode ser influenciado pelos vereditos automáticos. Por isso o painel esconde os vereditos durante a avaliação.
- **Generalização indevida:** os resultados valem para este conjunto e estes modelos. Não devem ser usados para afirmar que um modelo é melhor em geral.
