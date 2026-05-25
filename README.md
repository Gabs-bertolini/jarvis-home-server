# Jarvis AI Assistant

Assistente pessoal local inspirado no Jarvis do Homem de Ferro, rodando com LLM local, memória persistente em JSON e possibilidade de automação de ações no servidor.

## Features

- LLM local via Ollama
- Memória persistente em JSON
- Prompt dinâmico com contexto salvo
- Personalidade customizável
- Base para automações via Discord ou terminal
- Estrutura preparada para executar ações reais no servidor

## Estrutura do projeto

```bash
jarvis/
├── main.py
├── memory.py
├── memory.json
├── venv/
└── README.md
```

## Como funciona

Fluxo do sistema:

```text
Usuário -> Input terminal / Discord
        -> Carrega memória JSON
        -> Injeta memória no prompt
        -> Envia prompt para LLM local
        -> Recebe resposta
        -> Exibe resposta
        -> (futuramente executa ações)
```

A LLM não possui memória nativa persistente.

Para resolver isso, o projeto:
1. Salva informações importantes em `memory.json`
2. Carrega essas informações ao iniciar nova conversa
3. Injeta memória no prompt do modelo

## Requisitos

- Python 3.10+
- Ollama instalado
- Modelo local baixado

## Instalação

Clone o projeto:

```bash
git clone <repo-url>
cd jarvis
```

Crie ambiente virtual:

```bash
python3 -m venv venv
```

Ative:

Linux/macOS:

```bash
source venv/bin/activate
```

Windows:

```powershell
venv\Scripts\activate
```

Instale dependências:

```bash
pip install requests
```

## Ollama

Instale:

https://ollama.com

Baixe modelo:

```bash
ollama pull llama3
```

Inicie serviço:

```bash
ollama serve
```

## Configuração

Edite no `main.py`:

```python
MODEL = "llama3"
```

Troque para o modelo desejado.

## Executando

```bash
python main.py
```

## Uso

Exemplo:

```text
Voce: qual meu nome?
Jarvis: Seu nome é Gabriel.
```

Salvar memória:

```text
Voce: remember favorite_server=minecraft
```

Consultar:

```text
Voce: qual meu servidor favorito?
Jarvis: Seu servidor favorito é minecraft.
```

## Exemplo de memória

Arquivo `memory.json`:

```json
{
    "name": "Gabriel",
    "favorite_server": "minecraft"
}
```

## Próximas features

- [ ] Integração com Discord bot
- [ ] Execução de ações no servidor
- [ ] Function calling
- [ ] Memória automática sem comando `remember`
- [ ] Histórico de conversas
- [ ] Dashboard web
- [ ] Alertas de infraestrutura

## Possíveis automações futuras

Comandos planejados:

```text
jarvis start minecraft
jarvis stop minecraft
jarvis server status
jarvis backup now
jarvis docker logs api
```

## Segurança

O projeto **não deve executar comandos arbitrários diretamente da LLM**.

Use whitelist de ações:

```python
ACTIONS = {
    "server_status": server_status,
    "start_minecraft": start_minecraft
}
```

Isso evita execução indevida.

## Tecnologias

- Python
- Ollama
- JSON
- Requests

## Inspiração

Projeto inspirado no conceito de assistente pessoal local estilo Jarvis, combinando:

- LLM local
- automação
- DevOps
- infraestrutura pessoal

---

Made with coffee, Linux and questionable sleep schedule.

## FastAPI

Instale as dependências do FastAPI:

```bash
pip install -r requirements.txt
```

Inicie o servidor:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

A API ficará disponível em `http://127.0.0.1:8000`.

Endpoints:

- `POST /chat` com JSON `{ "message": "Olá" }`
- `GET /memory` para ler a memória atual
- `POST /remember` com JSON `{ "key": "foo", "value": "bar" }`
- `GET /server-status` para ver o status do servidor
