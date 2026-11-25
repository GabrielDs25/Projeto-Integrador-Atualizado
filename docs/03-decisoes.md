# 3. Decisões de arquitetura

Registros curtos no formato contexto, decisão, alternativas descartadas e consequências.

## ADR 1: Modelos abertos locais com Ollama

**Contexto.** O projeto precisa ter custo zero e permitir que qualquer pessoa reproduza os resultados. APIs comerciais cobram por token, exigem chave e mudam de versão sem aviso, o que atrapalha a reprodutibilidade.

**Decisão.** Todos os modelos, avaliados e juiz, rodam localmente no Ollama, com temperatura 0 e seed 42.

**Alternativas descartadas.**
- *APIs pagas (OpenAI, Anthropic, Google):* custo, chave secreta no repositório e versões fora do nosso controle.
- *Hugging Face Transformers direto:* mais configuração e mais memória, sem ganho para o objetivo do projeto.

**Consequências.** Os modelos são pequenos (3 a 7 bilhões de parâmetros) e lentos em CPU. Os resultados valem para esses modelos, não para modelos comerciais maiores.

## ADR 2: Juiz maior e de família diferente dos avaliados

**Contexto.** Um juiz que avalia as próprias respostas tende a favorecê-las. Um juiz menor que os avaliados pode não ter conhecimento suficiente para julgar.

**Decisão.** O juiz padrão é o `qwen2.5:7b`, maior que todos os avaliados (3 a 4 bilhões de parâmetros). Ele recebe a resposta de referência junto com a pergunta, responde em JSON e tem o prompt versionado (`juiz-v1`, gravado em cada execução).

**Alternativas descartadas.**
- *Usar o próprio modelo avaliado como juiz:* risco de autoavaliação favorável.
- *Juiz sem resposta de referência:* o juiz dependeria só do próprio conhecimento, o que aumenta o erro.
- *Nota de 1 a 5 em vez de aprovado/reprovado:* dificulta comparar com o baseline e com a nota humana e calcular o kappa.

**Consequências.** O juiz é o passo mais lento da bateria. O `qwen2.5:3b` avaliado é da mesma família do juiz, um possível viés que tratamos como limitação.

## ADR 3: Bateria em duas fases

**Contexto.** Intercalar resposta e julgamento caso a caso faz o Ollama trocar o modelo avaliado e o juiz na memória a cada pergunta. Em uma máquina com 8 GB e sem GPU, os dois modelos não cabem juntos e cada troca leva segundos.

**Decisão.** Primeiro o modelo avaliado responde a todos os casos (fase 1). Depois ele é descarregado (`keep_alive=0`) e o juiz avalia todas as respostas (fase 2). Cada resposta é gravada no banco assim que gerada.

**Alternativas descartadas.**
- *Fases intercaladas:* muito mais lento em máquinas modestas.
- *Processamento paralelo:* não cabe na memória disponível.

**Consequências.** Se a bateria for interrompida na fase 2, as respostas da fase 1 já estão salvas, mas parte dos vereditos fica vazia.

## ADR 4: SQLite como armazenamento

**Contexto.** É preciso guardar execuções, respostas, vereditos e notas humanas, consultá-los no painel e na CLI e exportá-los como evidência.

**Decisão.** Usar um único arquivo SQLite (`eval/avaliacoes.db`), com uma tabela de execuções e outra de resultados, e migração automática de colunas.

**Alternativas descartadas.**
- *Arquivos CSV ou JSON:* sem consultas, sem atualização segura das notas humanas e com risco de corromper o arquivo.
- *PostgreSQL:* exigiria mais um serviço para instalar, sem necessidade para um único usuário local.

**Consequências.** Não suporta muitos usuários escrevendo ao mesmo tempo, o que não é um requisito. Para gerar evidências, os dados são exportados em CSV e JSON com `exportar`.

## ADR 5: Baseline por palavra-chave e humano como referência

**Contexto.** Para saber se o juiz é bom, ele precisa ser comparado com algo mais simples (baseline) e com uma referência confiável (pessoas). Ajustar o juiz e medi-lo nos mesmos casos inflaria o resultado.

**Decisão.**
- O baseline aprova a resposta se ela contém, como termo inteiro, uma das palavras-chave esperadas, sem diferenciar acentos nem maiúsculas.
- A nota humana é a verdade de referência e é dada no painel sem mostrar o veredito do juiz.
- Os casos têm divisão fixa: 30 de calibração (para ajustar o prompt do juiz) e 70 de teste (só para medir).

**Alternativas descartadas.**
- *Similaridade de texto (BLEU, ROUGE, embeddings):* exige mais dependências e é pouco interpretável para respostas curtas.
- *Comparar o juiz só com o baseline:* o baseline também erra, por exemplo com negações.
- *Divisão aleatória dos casos:* mudaria a cada geração. A divisão fixa garante reprodutibilidade.

**Consequências.** As métricas de concordância só existem depois que o grupo avalia as respostas à mão (no mínimo 30).
