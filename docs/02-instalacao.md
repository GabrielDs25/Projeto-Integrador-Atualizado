# 2. Instalação e execução

Tudo roda localmente, com modelos abertos via [Ollama](https://ollama.com). Não há chave de API nem custo.

## Requisitos de hardware

| Recurso | Mínimo | Observação |
|---|---|---|
| Memória RAM | 8 GB | O juiz `qwen2.5:7b` ocupa cerca de 5 GB. Por isso a bateria descarrega o modelo avaliado antes de carregar o juiz. |
| Disco | ~12 GB livres | Os quatro modelos somados |
| GPU | Opcional | Sem GPU tudo funciona, só mais devagar. Medimos cerca de 15 s por resposta e 30 a 50 s por veredito do juiz em CPU. |

## Opção 1: Docker (recomendada)

Pré-requisito: [Docker](https://docs.docker.com/get-docker/) com Docker Compose.

```bash
docker compose up
```

O `docker-compose.yml` sobe três serviços:

| Serviço | Função |
|---|---|
| `ollama` | Servidor de modelos. Os modelos ficam no volume `ollama` e não são baixados de novo. |
| `baixar-modelos` | Executa `ollama pull` para cada modelo configurado e termina. Na primeira vez baixa cerca de 12 GB. |
| `app` | Painel Streamlit em http://localhost:8501. Só sobe depois que os modelos foram baixados. |

As pastas `eval/` e `evidencias/` são montadas no container, então o banco, os logs e as imagens geradas ficam no seu disco.

Para rodar comandos da CLI dentro do container:

```bash
docker compose exec app python -m src.cli rodar --versao v1
docker compose exec app python -m src.cli execucoes
```

## Opção 2: execução local

Pré-requisitos: Python 3.11 ou superior e o Ollama instalado e em execução.

```bash
# 1. Modelos
ollama pull gemma3:4b
ollama pull llama3.2:3b
ollama pull qwen2.5:3b
ollama pull qwen2.5:7b

# 2. Ambiente Python
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt

# 3. Painel
python -m streamlit run src/app.py
```

Os comandos devem ser executados a partir da **raiz do repositório**, porque o código importa os módulos como `src.*`.

## Variáveis de ambiente

Nenhuma é obrigatória. Para mudar os padrões, copie [.env.example](../.env.example) para `.env` (o Docker Compose lê esse arquivo) ou defina as variáveis no terminal.

| Variável | Padrão | Uso |
|---|---|---|
| `MODELOS_AVALIADOS` | `gemma3:4b,llama3.2:3b,qwen2.5:3b` | Modelos comparados, separados por vírgula |
| `MODELO_JUIZ` | `qwen2.5:7b` | Modelo usado como juiz |
| `OLLAMA_HOST` | `http://localhost:11434` (no Docker: `http://ollama:11434`) | Endereço do servidor Ollama |
| `DATABASE_PATH` | `eval/avaliacoes.db` | Arquivo do banco SQLite |

## Verificação da instalação

```bash
python -m src.cli rodar --versao v1 --limite 3 --modelos qwen2.5:3b --descricao "verificacao"
python -m src.cli execucoes
pytest
```

Se a bateria terminar com "Execuções criadas" e os testes passarem, a instalação está correta.

## Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| `Modelos não instalados no Ollama: ...` (código de saída 2) | Rode `ollama pull <modelo>` para cada modelo listado. |
| `Não foi possível acessar o Ollama` | O Ollama não está rodando ou `OLLAMA_HOST` aponta para outro endereço. Inicie o Ollama ou ajuste a variável. |
| `ModuleNotFoundError: No module named 'src'` | O comando foi executado fora da raiz do repositório. |
| Bateria muito lenta ou máquina travando | Pouca memória. Use `--limite N` para testar, feche outros programas ou use um juiz menor com `--juiz qwen2.5:3b` (registre essa mudança, porque ela altera os resultados). |
| Acentos quebrados no terminal do Windows | A CLI já configura UTF-8. Se persistir, rode `chcp 65001` antes. |
