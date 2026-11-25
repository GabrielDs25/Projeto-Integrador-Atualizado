# 9. Manual do usuário

Passo a passo para avaliar uma nova versão de prompt, do início ao resultado.

> As capturas de tela ficam em [evidencias/capturas/](../evidencias/capturas/).

## Passo 1: abrir o painel

Com o projeto instalado (ver [Instalação e execução](02-instalacao.md)):

```bash
docker compose up
# ou, localmente:
python -m streamlit run src/app.py
```

Acesse http://localhost:8501. No topo há cinco visões: **Resultados por versão**, **Regressão**, **Avaliação humana**, **Juiz × humano** e **Pergunta livre**.

Se ainda não houver baterias, o painel mostra o aviso "Sem dados" com o comando para rodar a primeira.

![Painel sem dados](../evidencias/capturas/01-painel-inicial.png)

## Passo 2: rodar uma bateria

As baterias são iniciadas pela linha de comando:

```bash
python -m src.cli rodar --versao v1 --descricao "oficial v1"
```

O terminal mostra o progresso a cada 10 casos e, ao final, a taxa de acerto de cada modelo. Para criar uma nova versão de prompt, adicione um arquivo `eval/prompts/vN.txt` e rode com `--versao vN`.

![Bateria em execução no terminal](../evidencias/capturas/02-bateria-terminal.png)

## Passo 3: ver os resultados por versão

Na visão **Resultados por versão**:

1. O gráfico mostra a taxa de acerto do juiz para cada modelo, com uma cor por versão de prompt.
2. A tabela "Todas as execuções" traz casos, taxas (juiz, baseline e humano), tempo, tokens e erros.
3. Em "Detalhes de uma execução", escolha uma execução para ver cada pergunta, a resposta do modelo, os vereditos e a justificativa do juiz.

![Resultados por versão](../evidencias/capturas/03-resultados.png)

## Passo 4: verificar se houve regressão

Na visão **Regressão**:

1. Em "Execução base", escolha a execução de referência (por exemplo, `v1`).
2. Em "Execução nova", escolha a nova versão do mesmo modelo (por exemplo, `v2_piorado`).
3. Ajuste o limiar se necessário (padrão: 5 pontos percentuais).

O painel mostra as duas taxas, a variação e o número de casos que pioraram. Uma caixa vermelha indica **Regressão detectada**. Uma verde indica que a variação está dentro do limiar.

![Regressão detectada](../evidencias/capturas/04-regressao.png)

Pela linha de comando, o equivalente é `python -m src.cli comparar <base> <nova>`.

## Passo 5: avaliar respostas à mão

Na visão **Avaliação humana**:

1. Escolha a execução e digite seu nome no campo "Seu nome (avaliador)".
2. Para cada resposta, leia a pergunta, a referência e a resposta do modelo e escolha **Aprovada** ou **Reprovada** na coluna "nota". O veredito do juiz não aparece, para não influenciar a sua nota.
3. Clique em **Salvar avaliações**. O contador mostra quantas respostas já foram avaliadas.

Avalie pelo menos 30 respostas para que a concordância tenha significado.

![Avaliação humana](../evidencias/capturas/05-avaliacao-humana.png)

## Passo 6: medir a concordância do juiz

Na visão **Juiz × humano**:

1. Selecione as execuções consideradas (por padrão, todas).
2. Os dois quadros mostram, para o juiz e para o baseline: número de casos, acordo percentual, kappa de Cohen com a interpretação e matriz de confusão.
3. A tabela "Casos em que o juiz errou" lista as divergências com a justificativa do juiz, que servem de base para a análise de erros.

![Juiz × humano](../evidencias/capturas/06-juiz-humano.png)

## Passo 7: fazer uma pergunta livre (opcional)

Na visão **Pergunta livre**, escolha os modelos, digite uma pergunta e clique em **Perguntar**. Cada modelo responde em um quadro, com o tempo e os tokens. Essas perguntas não entram nas métricas das baterias.

![Pergunta livre](../evidencias/capturas/07-pergunta-livre.png)

## Passo 8: gerar as evidências

```bash
python -m src.cli exportar <ids...>   # CSV e metricas.json em eval/resultados/
python -m src.cli erros <ids...>      # imagens dos casos de falha em evidencias/erros/
```

Depois, abra `evidencias/erros/README.md` e preencha a coluna "Causa provável" de cada caso. O texto preenchido é mantido quando o comando roda de novo.
