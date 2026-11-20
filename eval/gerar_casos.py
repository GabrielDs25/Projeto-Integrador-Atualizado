"""Gera eval/casos.json a partir da lista abaixo.

Cada caso tem: pergunta, resposta de referência e palavras-chave aceitas
pelo baseline (comparação por palavra-chave, sem acentos e sem diferenciar
maiúsculas). A divisão é fixa e determinística: em cada bloco de 10 casos,
os 3 primeiros vão para "calibracao" (usados para ajustar o prompt do juiz)
e os 7 restantes para "teste" (nunca usados para ajuste).

Uso: python eval/gerar_casos.py
"""

import json
from pathlib import Path

CASOS = [
    # --- Python (1-30) ---
    ("python", "Qual a saída de print(2 ** 3) em Python?", "8", ["8", "oito"]),
    ("python", "Qual função embutida do Python retorna o número de elementos de uma lista?", "len()", ["len"]),
    ("python", "Qual o resultado de 7 // 2 em Python?", "3", ["3", "tres"]),
    ("python", "Qual o resultado de 7 % 3 em Python?", "1", ["1", "um"]),
    ("python", "Qual palavra-chave define uma função em Python?", "def", ["def"]),
    ("python", "Qual o tipo do valor 3.14 em Python?", "float", ["float"]),
    ("python", 'Qual o resultado de len("banana") em Python?', "6", ["6", "seis"]),
    ("python", "Qual método de lista adiciona um elemento ao final da lista em Python?", "append()", ["append"]),
    ("python", "O que retorna bool([]) em Python?", "False", ["false"]),
    ("python", "Qual palavra-chave captura exceções em um bloco try em Python?", "except", ["except"]),
    ("python", 'Qual o resultado de "abc"[::-1] em Python?', "'cba'", ["cba"]),
    ("python", "Qual o nome do tipo do valor None em Python?", "NoneType", ["nonetype"]),
    ("python", "Qual palavra-chave cria uma função anônima em Python?", "lambda", ["lambda"]),
    ("python", "Qual o resultado de list(range(3)) em Python?", "[0, 1, 2]", ["0, 1, 2", "0,1,2"]),
    ("python", "Tuplas em Python são mutáveis ou imutáveis?", "Imutáveis", ["imutavel", "imutaveis", "immutable"]),
    ("python", "Qual comando instala pacotes Python a partir do PyPI?", "pip install", ["pip"]),
    ("python", "Qual o resultado de 10 / 4 em Python 3?", "2.5", ["2.5", "2,5"]),
    ("python", "Qual palavra-chave transforma uma função em gerador em Python?", "yield", ["yield"]),
    ("python", "Qual método de string converte todas as letras para maiúsculas em Python?", "upper()", ["upper"]),
    ("python", 'Qual o resultado de "Py" * 3 em Python?', "'PyPyPy'", ["pypypy"]),
    ("python", "Qual estrutura de dados embutida do Python armazena pares chave-valor?", "Dicionário (dict)", ["dict", "dicionario"]),
    ("python", "Qual o resultado de sorted([3, 1, 2]) em Python?", "[1, 2, 3]", ["1, 2, 3", "1,2,3"]),
    ("python", 'Qual função embutida converte a string "42" no número inteiro 42 em Python?', "int()", ["int"]),
    ("python", "Qual operador do Python verifica se duas variáveis referenciam o mesmo objeto?", "is", ["is"]),
    ("python", "Qual arquivo marca, tradicionalmente, um diretório como pacote Python?", "__init__.py", ["__init__.py", "__init__"]),
    ("python", "Qual PEP define o guia de estilo de código Python?", "PEP 8", ["pep 8", "pep8", "pep-8"]),
    ("python", "O que imprime print(0.1 + 0.2 == 0.3) em Python?", "False", ["false"]),
    ("python", "Quantos elementos tem o conjunto set([1, 1, 2]) em Python?", "2", ["2", "dois"]),
    ("python", "Qual palavra-chave do Python é usada com gerenciadores de contexto, como ao abrir arquivos?", "with", ["with"]),
    ("python", "Qual o resultado de max([4, 9, 2]) em Python?", "9", ["9", "nove"]),
    # --- Algoritmos e estruturas de dados (31-50) ---
    ("algoritmos", "Qual a complexidade de tempo da busca binária em um vetor ordenado?", "O(log n)", ["o(log n)", "log n", "logaritmica"]),
    ("algoritmos", "Qual estrutura de dados segue a política LIFO (último a entrar, primeiro a sair)?", "Pilha", ["pilha", "stack"]),
    ("algoritmos", "Qual estrutura de dados segue a política FIFO (primeiro a entrar, primeiro a sair)?", "Fila", ["fila", "queue"]),
    ("algoritmos", "Qual a complexidade de tempo do quicksort no caso médio?", "O(n log n)", ["n log n"]),
    ("algoritmos", "Qual a complexidade de tempo do bubble sort no pior caso?", "O(n²)", ["n^2", "n²", "n2", "quadratica"]),
    ("algoritmos", "Quantas arestas tem uma árvore com 10 vértices?", "9", ["9", "nove"]),
    ("algoritmos", "Qual algoritmo clássico encontra caminhos mínimos em grafos com pesos não negativos e leva o nome de um cientista holandês?", "Algoritmo de Dijkstra", ["dijkstra"]),
    ("algoritmos", "Qual estrutura de dados auxiliar é usada na busca em largura (BFS)?", "Fila", ["fila", "queue"]),
    ("algoritmos", "Qual estrutura de dados auxiliar é usada em uma busca em profundidade (DFS) iterativa?", "Pilha", ["pilha", "stack"]),
    ("algoritmos", "Qual a complexidade de tempo do acesso por índice em um array?", "O(1)", ["o(1)", "constante"]),
    ("algoritmos", "Quantos bits tem um byte?", "8", ["8", "oito"]),
    ("algoritmos", "Qual o valor decimal do número binário 1010?", "10", ["10", "dez"]),
    ("algoritmos", "Qual a representação hexadecimal do número decimal 255?", "FF", ["ff", "0xff"]),
    ("algoritmos", "Como se chama a técnica que resolve um problema guardando resultados de subproblemas para reutilizá-los?", "Programação dinâmica", ["programacao dinamica", "memoizacao", "dynamic programming"]),
    ("algoritmos", "Qual algoritmo de ordenação divide a lista ao meio, ordena cada metade e depois intercala as duas?", "Merge sort (ordenação por intercalação)", ["merge sort", "mergesort", "intercalacao"]),
    ("algoritmos", "Qual estrutura de dados é normalmente usada para implementar filas de prioridade, com inserção e remoção do mínimo em O(log n)?", "Heap", ["heap", "monte"]),
    ("algoritmos", "Quanto é 2 elevado a 10?", "1024", ["1024", "1.024"]),
    ("algoritmos", "Como se chama a estrutura que usa uma função para mapear chaves em posições de um vetor?", "Tabela hash (tabela de dispersão)", ["hash", "dispersao"]),
    ("algoritmos", "O que é recursão em programação?", "Quando uma função chama a si mesma", ["chama a si mesma", "chama a propria", "si mesma"]),
    ("algoritmos", "Qual a complexidade de tempo da busca linear em uma lista com n elementos?", "O(n)", ["o(n)", "linear"]),
    # --- Web e redes (51-65) ---
    ("web", "O que significa a sigla HTTP?", "HyperText Transfer Protocol (Protocolo de Transferência de Hipertexto)", ["hypertext transfer protocol", "protocolo de transferencia de hipertexto"]),
    ("web", "Qual código de status HTTP indica que o recurso não foi encontrado?", "404", ["404"]),
    ("web", "Qual código de status HTTP indica sucesso padrão de uma requisição?", "200", ["200"]),
    ("web", "Qual a porta padrão do HTTPS?", "443", ["443"]),
    ("web", "Qual método HTTP é normalmente usado para criar um recurso em uma API REST?", "POST", ["post"]),
    ("web", "Qual protocolo traduz nomes de domínio em endereços IP?", "DNS", ["dns"]),
    ("web", "Qual código de status HTTP indica erro interno do servidor?", "500", ["500"]),
    ("web", "O que significa a sigla JSON?", "JavaScript Object Notation", ["javascript object notation"]),
    ("web", "Quantos bits tem um endereço IPv4?", "32", ["32"]),
    ("web", "Qual linguagem de marcação é usada para estruturar páginas web?", "HTML", ["html"]),
    ("web", "Qual a porta padrão do SSH?", "22", ["22"]),
    ("web", "Qual código de status HTTP indica falta de autenticação (não autorizado)?", "401", ["401"]),
    ("web", "Qual linguagem é usada para definir o estilo visual de páginas web?", "CSS", ["css"]),
    ("web", "O que significa a sigla API?", "Application Programming Interface (Interface de Programação de Aplicações)", ["application programming interface", "interface de programacao de aplicacoes", "interface de programacao de aplicacao"]),
    ("web", "Qual método HTTP é usado para remover um recurso em uma API REST?", "DELETE", ["delete"]),
    # --- Git e DevOps (66-80) ---
    ("devops", "Qual comando Git cria uma cópia local de um repositório remoto?", "git clone", ["clone"]),
    ("devops", "Qual comando Git registra no histórico as alterações preparadas (staged)?", "git commit", ["commit"]),
    ("devops", "Qual comando Git envia os commits locais para o repositório remoto?", "git push", ["push"]),
    ("devops", "Qual comando Git mostra o estado dos arquivos do diretório de trabalho?", "git status", ["status"]),
    ("devops", "Qual arquivo lista os arquivos que o Git deve ignorar?", ".gitignore", ["gitignore"]),
    ("devops", "Qual comando Git cria uma nova branch e já muda para ela?", "git switch -c <nome> (ou git checkout -b <nome>)", ["switch -c", "checkout -b"]),
    ("devops", "Qual arquivo descreve como construir uma imagem Docker?", "Dockerfile", ["dockerfile"]),
    ("devops", "Qual comando sobe os serviços definidos em um arquivo docker-compose.yml?", "docker compose up", ["compose up", "docker-compose up"]),
    ("devops", "O que significa a sigla CI em engenharia de software?", "Integração contínua (Continuous Integration)", ["integracao continua", "continuous integration"]),
    ("devops", "Em qual formato de arquivo são escritos os workflows do GitHub Actions?", "YAML", ["yaml", "yml"]),
    ("devops", "Qual comando Git baixa as alterações do remoto e as integra à branch atual?", "git pull", ["pull"]),
    ("devops", "Qual comando Docker lista os containers em execução?", "docker ps", ["docker ps", "docker container ls"]),
    ("devops", "Qual sistema de orquestração de containers foi criado originalmente pelo Google?", "Kubernetes", ["kubernetes", "k8s"]),
    ("devops", "No versionamento semântico (MAJOR.MINOR.PATCH), qual componente deve ser incrementado quando há uma mudança incompatível na API?", "MAJOR", ["major"]),
    ("devops", "Qual comando Git mostra o histórico de commits?", "git log", ["log"]),
    # --- Banco de dados (81-90) ---
    ("banco_dados", "Qual comando SQL é usado para consultar dados de uma tabela?", "SELECT", ["select"]),
    ("banco_dados", "Qual cláusula SQL filtra as linhas retornadas por uma consulta?", "WHERE", ["where"]),
    ("banco_dados", "Qual comando SQL remove uma tabela inteira, incluindo sua estrutura?", "DROP TABLE", ["drop"]),
    ("banco_dados", "Qual cláusula SQL agrupa linhas para aplicar funções de agregação?", "GROUP BY", ["group by"]),
    ("banco_dados", "Qual tipo de JOIN retorna apenas as linhas com correspondência nas duas tabelas?", "INNER JOIN", ["inner"]),
    ("banco_dados", "O que significa a sigla SQL?", "Structured Query Language", ["structured query language"]),
    ("banco_dados", "Qual restrição garante que uma coluna identifica unicamente cada linha de uma tabela?", "Chave primária (PRIMARY KEY)", ["chave primaria", "primary key"]),
    ("banco_dados", "Qual função de agregação SQL conta linhas?", "COUNT", ["count"]),
    ("banco_dados", "Qual comando SQL insere novas linhas em uma tabela?", "INSERT", ["insert"]),
    ("banco_dados", "Qual propriedade ACID garante que uma transação é executada por completo ou não é executada?", "Atomicidade", ["atomicidade", "atomicity"]),
    # --- Inteligência artificial (91-100) ---
    ("ia", "O que significa a sigla LLM?", "Large Language Model (grande modelo de linguagem)", ["large language model", "modelo de linguagem de grande", "grande modelo de linguagem", "modelo de linguagem grande"]),
    ("ia", "O que significa a sigla RAG no contexto de LLMs?", "Retrieval-Augmented Generation (geração aumentada por recuperação)", ["retrieval-augmented generation", "retrieval augmented generation", "geracao aumentada"]),
    ("ia", "Como se chama, em aprendizado de máquina, quando o modelo memoriza os dados de treino e generaliza mal?", "Overfitting (sobreajuste)", ["overfitting", "sobreajuste"]),
    ("ia", "Qual métrica é a média harmônica entre precisão e recall?", "F1-score", ["f1", "f1-score", "f-score"]),
    ("ia", "Que tipo de aprendizado de máquina usa dados rotulados?", "Aprendizado supervisionado", ["supervisionado", "supervised"]),
    ("ia", 'Qual arquitetura de rede neural, apresentada no artigo "Attention Is All You Need", é a base dos LLMs modernos?', "Transformer", ["transformer", "transformers"]),
    ("ia", "Como se chama a unidade básica de texto processada por um LLM?", "Token", ["token", "tokens"]),
    ("ia", "Qual estatística mede a concordância entre dois avaliadores descontando a concordância esperada ao acaso?", "Kappa de Cohen", ["kappa"]),
    ("ia", "Como se chama uma resposta incorreta ou inventada apresentada com confiança por um LLM?", "Alucinação", ["alucinacao", "alucinacoes", "hallucination"]),
    ("ia", "Qual parâmetro de geração controla a aleatoriedade das respostas de um LLM?", "Temperatura", ["temperatura", "temperature"]),
]


def main():
    casos = []
    for indice, (categoria, pergunta, referencia, chaves) in enumerate(CASOS, start=1):
        casos.append({
            "id": f"C{indice:03d}",
            "split": "calibracao" if (indice - 1) % 10 < 3 else "teste",
            "categoria": categoria,
            "pergunta": pergunta,
            "resposta_referencia": referencia,
            "palavras_chave": chaves,
        })

    destino = Path(__file__).resolve().parent / "casos.json"
    destino.write_text(
        json.dumps(casos, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{len(casos)} casos gravados em {destino}")


if __name__ == "__main__":
    main()
