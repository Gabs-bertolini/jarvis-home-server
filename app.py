import json
import os
import hmac
import hashlib
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import requests
from requests.exceptions import RequestException, Timeout
from memory import load_memory, update_memory
from actions import server_status, docker_status

load_dotenv()

MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://192.168.0.211:11434")
BASE_DIR = Path(__file__).resolve().parent
MEMORY_FILE = BASE_DIR / "memory.json"
DISCORD_WEBHOOK_TOKEN = os.getenv("DISCORD_WEBHOOK_TOKEN")

app = FastAPI(title="Jarvis Home Server", version="1.0")


class ChatRequest(BaseModel):
    message: str


class RememberRequest(BaseModel):
    key: str
    value: str


def build_prompt(user_message: str) -> str:
    memory = load_memory()
    system_prompt = f"""\
Você é Jarvis, meu assistente pessoal de infraestrutura.

Memória persistente do usuário:
{json.dumps(memory, indent=4, ensure_ascii=False)}

Você possui ações disponíveis.

Ações disponíveis:
- normal_chat
- server_status
- docker_status

REGRAS:
- Responda SEMPRE em JSON válido.
- Nunca escreva texto fora do JSON.

Formato para conversa normal:
{
    "action": "normal_chat",
    "message": "resposta aqui"
}

Formato para status:
{
    "action": "server_status"
}
"""
    return system_prompt + "\nUsuário: " + user_message


def ask_llm(prompt: str) -> str:
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except Timeout as exc:
        raise HTTPException(status_code=504, detail=f"LLM request timed out: {exc}")
    except RequestException as exc:
        raise HTTPException(status_code=502, detail=f"LLM request failed: {exc}")


def process_response(response: str) -> dict:
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        json_str = response[start:end]
        return json.loads(json_str)
    except Exception:
        return {"action": "normal_chat", "message": response}


def _process_chat_message(message: str) -> dict:
    prompt = build_prompt(message)
    raw_response = ask_llm(prompt)
    parsed = process_response(raw_response)
    action = parsed.get("action")

    if action == "server_status":
        raw_status = server_status()
        summary_prompt = f"""\
Analise e resuma de forma objetiva o status abaixo do servidor:

{raw_status}
"""
        summary = ask_llm(summary_prompt)
        return {
            "action": "server_status",
            "status": raw_status,
            "summary": summary,
            "raw_response": raw_response,
        }

    if action == "docker_status":
        raw_status = docker_status()
        summary_prompt = f"""\
Analise e resuma de forma objetiva o status abaixo do docker:

{raw_status}
"""
        summary = ask_llm(summary_prompt)
        return {
            "action": "docker_status",
            "status": raw_status,
            "summary": summary,
            "raw_response": raw_response,
        }

    if action == "normal_chat":
        return {
            "action": "normal_chat",
            "message": parsed.get("message", "Sem resposta."),
            "raw_response": raw_response,
        }

    return {
        "action": "unknown",
        "message": "Ação desconhecida.",
        "raw_response": raw_response,
    }


@app.get("/jarvis")
async def root():
    return {"message": "Jarvis FastAPI server is running."}


@app.post("/jarvis/chat")
async def chat(request: ChatRequest):
    return _process_chat_message(request.message)


from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

# 1. PEGUE A SUA "PUBLIC KEY" (NÃO É O TOKEN!)
# Vá na aba "General Information" do painel do Discord e copie o campo "PUBLIC KEY"
DISCORD_PUBLIC_KEY = os.getenv("DISCORD_PUBLIC_KEY", "COLE_AQUI_SUA_PUBLIC_KEY_SE_NAO_USAR_ENV")

@app.post("/discord/webhook")
async def discord_webhook(request: Request):
    # --- PASSO OBRIGATÓRIO DO DISCORD: VERIFICAÇÃO CRIPTOGRÁFICA ED25519 ---
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")
    
    # Se não tiver assinatura e tiver o seu token customizado, assume que é o seu cURL manual antigo
    token = request.headers.get("X-Discord-Token")
    is_manual_curl = token == DISCORD_WEBHOOK_TOKEN and token is not None

    body = await request.body()

    if not is_manual_curl:
        if not signature or not timestamp:
            raise HTTPException(status_code=401, detail="Missing Discord signatures")
        
        try:
            # Valida matematicamente se a requisição veio mesmo do servidor do Discord
            verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
            verify_key.verify(f"{timestamp}".encode() + body, bytes.fromhex(signature))
        except BadSignatureError:
            raise HTTPException(status_code=401, detail="Invalid request signature")
    # ------------------------------------------------------------------------

    # Parse do JSON após passar na segurança
    try:
        data = json.loads(body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Responder ao PING de validação do Discord para salvar a URL
    if data.get("type") == 1:
        return {"type": 1}

    # Processamento do conteúdo das mensagens (Manual ou Slash Command)
    content = ""
    if "content" in data:
        content = data.get("content", "")
    elif data.get("type") == 2:
        try:
            # Captura o valor digitado no comando do Discord
            options = data["data"].get("options", [])
            if options:
                content = options[0].get("value", "") # Pega o valor do primeiro argumento
        except Exception:
            content = ""

    if not content:
        raise HTTPException(status_code=400, detail="Missing 'content' or command input in request")

    # Executa a sua LLM (Jarvis)
    jarvis_result = _process_chat_message(content)
    
    # Formata o retorno para o Discord se for uma interação oficial
    if data.get("type") == 2:
        reply_text = jarvis_result.get("message") or jarvis_result.get("summary") or "Jarvis processou o comando."
        return {
            "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
            "data": {
                "content": reply_text
            }
        }
        
    return jarvis_result

@app.get("/jarvis/memory")
async def get_memory():
    return load_memory()


@app.post("/jarvis/remember")
async def remember(request: RememberRequest):
    try:
        update_memory(request.key, request.value)
        return {"status": "ok", "key": request.key, "value": request.value}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/jarvis/server-status")
async def get_server_status():
    try:
        raw_status = server_status()
        return {"status": raw_status}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))