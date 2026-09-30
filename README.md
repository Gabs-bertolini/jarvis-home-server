# Jarvis Home Server

Assistente pessoal local para infraestrutura doméstica, com IA local via Ollama, memória persistente em JSON e integração com FastAPI e Discord. A aplicação recebe mensagens, injeta contexto de memória no prompt, consulta o modelo local e decide se responde em conversa normal ou coleta dados do servidor e do Docker para resumir o estado atual.

## Visão geral

Este projeto funciona como um "Jarvis leve" para monitorar um ambiente Linux/servidor local. Ele combina:

- IA local via Ollama
- memória persistente em JSON
- API HTTP para integração
- bot do Discord para interação em chat
- coleta de status do sistema e containers

Na prática, ele não executa comandos arbitrários no servidor; ele organiza as ações em fluxo controlado: a IA responde em JSON e o backend chama funções específicas como leitura de status do sistema ou do Docker.

## Como a aplicação funciona hoje

O fluxo principal é este:

1. A mensagem chega por API, bot do Discord ou terminal.
2. O sistema carrega a memória do arquivo memory.json.
3. O conteúdo e o contexto são montados em um prompt para a IA local.
4. O modelo responde com JSON, normalmente no formato:

```json
{
  "action": "normal_chat",
  "message": "resposta aqui"
}
```

ou, quando o usuário pede contexto de infraestrutura:

```json
{
  "action": "server_status"
}
```

5. O backend interpreta a ação e, se necessário, chama funções de monitoramento.
6. O resultado bruto é enviado novamente à IA para analisar e resumir de forma legível.
7. A resposta final é devolvida ao cliente em JSON ou em texto de chat.

## Arquitetura real do projeto

### Modos de execução

- app.py: API FastAPI principal.
- bot.py: bot do Discord com slash command /chat.
- main.py: interface de terminal, usada como protótipo ou teste manual.
- memory.py: leitura e gravação da memória em JSON.
- actions.py: coleta de status do servidor e Docker.
- Dockerfile: imagem para rodar a API em container.
- jarvis.nomad.hcl: configuração de deploy via Nomad.

### Funções principais

- build_prompt(): monta o prompt do modelo com memória e instruções de ação.
- ask_llm(): chama a API do Ollama.
- process_response(): extrai JSON da resposta da IA.
- _process_chat_message(): decide se a mensagem é conversa normal, status do servidor ou status do Docker.
- server_status(): coleta métricas do Glances.
- docker_status(): executa docker ps.
- update_memory(): salva informações no arquivo memory.json.

## Fluxo de memória

A LLM não tem memória persistente nativa. Esse projeto resolve isso com um arquivo JSON:

```json
{
  "name": "Gabriel",
  "favorite_server": "minecraft",
  "favorite_movie": "fightclub"
}
```

Esse contexto é lido a cada chamada e injetado no prompt do modelo, então a IA consegue responder com base no perfil do usuário e em informações salvas.

## Ações disponíveis

A IA opera com ações pré-definidas, em vez de executar comandos livres no sistema. As ações atuais são:

- normal_chat
- server_status
- docker_status

Isso mantém o fluxo controlado e evita execução arbitrária de comandos pelo modelo.

## Requisitos

- Python 3.11+
- Ollama instalado e rodando localmente
- Um modelo no Ollama, como llama3.2:3b
- Dependências do projeto
- Docker e/ou Glances conforme a rotina de monitoramento

## Variáveis de ambiente

Crie um arquivo .env na raiz do projeto com algo assim:

```env
OLLAMA_MODEL=llama3.2:3b
OLLAMA_HOST=http://192.168.0.211:11434
DISCORD_BOT_TOKEN=SEU_TOKEN_DO_BOT
DISCORD_PUBLIC_KEY=SUA_PUBLIC_KEY_DO_DISCORD
DISCORD_WEBHOOK_TOKEN=TOKEN_DO_WEBHOOK_OPCIONAL
```

Observações:

- O modelo default do projeto também é llama3.2:3b.
- O host do Ollama pode ser local ou remoto.
- O bot do Discord e o webhook exigem chaves vindas do painel do Discord.

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Se o Ollama ainda não estiver instalado:

```bash
# instalar Ollama
# depois baixar um modelo
ollama pull llama3.2:3b
```

E iniciar o serviço:

```bash
ollama serve
```

## Executando a API

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

A API fica em:

- http://localhost:8000
- http://127.0.0.1:8000

### Endpoints da API

- GET /jarvis
  - retorna confirmação de que a API está no ar
- POST /jarvis/chat
  - body:

```json
{
  "message": "Qual o status do servidor?"
}
```

- GET /jarvis/memory
  - retorna o conteúdo atual da memória
- POST /jarvis/remember
  - body:

```json
{
  "key": "favorite_server",
  "value": "minecraft"
}
```

- GET /jarvis/server-status
  - devolve status bruto do servidor em JSON
- POST /discord/webhook
  - endpoint para receber webhook ou interação do Discord

## Executando o bot do Discord

```bash
python bot.py
```

O bot começa com slash command /chat e usa a mesma lógica da IA para responder mensagens do Discord. Ele faz defer antes de processar para não expirar em chamadas longas.

## Executando em terminal

A aplicação possui um modo CLI em main.py, mas ele funciona mais como protótipo manual. A intenção principal do projeto é ficar em API + Discord.

```bash
python main.py
```

Comandos úteis de terminal:

```text
remember chave=valor
sair
```

## Monitoramento do sistema

O arquivo actions.py usa o Glances para coletar métricas e o Docker para listar containers ativos.

### Status do servidor

Ele envia uma requisição para:

```text
http://192.168.0.211:61208/api/4/all
```

E extrai:

- uso de CPU
- uso de memória
- uptime
- disco

### Status do Docker

Executa:

```bash
docker ps
```

 e retorna o resumo bruto para a IA processar.

## Segurança e limites

Este projeto é um assistente local com foco em monitoramento e resposta, não um executor genérico de comandos do sistema. Os pontos relevantes são:

- a IA não roda shell arbitrária
- as ações são um whitelist controlado
- o modelo apenas orienta o fluxo, e o backend decide o que chamar
- a execução de operações sensíveis precisa ser explicitamente implementada

## Estrutura padrão do repositório

```bash
jarvis-home-server/
├── actions.py
├── app.py
├── bot.py
├── Dockerfile
├── example-memory.json
├── jarvis.nomad.hcl
├── main.py
├── memory.py
├── memory.json
├── README.md
├── requirements.txt
└── .env
```

## Como o projeto se comporta na prática

Fluxo real de uso:

```text
Usuário -> HTTP / Discord
   -> IA local interpreta a intenção
   -> memória é carregada
   -> status do sistema é consultado quando necessário
   -> modelo resume o resultado em linguagem natural
   -> resposta retorna ao cliente
```

Em resumo: é uma base para um assistente pessoal de infraestrutura local, com foco em monitoramento, memória contextual e integração simples com APIs e Discord.

## Próxima evolução esperada

- melhorar o parsing da resposta da IA
- expandir a lista de ações controladas
- adicionar autenticação em endpoints sensíveis
- integrar mais serviços do sistema
- armazenar histórico de conversas
- criar um dashboard web

## Licença

Este projeto é um ambiente de estudo e automação doméstica local. Ajustes de segurança, autenticação e limites operacionais devem ser feitos conforme a sua infraestrutura real.


