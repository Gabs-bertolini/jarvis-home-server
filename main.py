import requests
import json
import os
from dotenv import load_dotenv
from memory import load_memory, update_memory
from actions import server_status

load_dotenv()

MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


def build_prompt(user_message):
    memory = load_memory()

    system_prompt = f"""
Você é Jarvis, meu assistente pessoal de infraestrutura.

Memória persistente do usuário:
{memory}

Você possui ações disponíveis.

Ações disponíveis:
- normal_chat
- server_status
- docker_status

REGRAS:
- Responda SEMPRE em JSON válido.
- Nunca escreva texto fora do JSON.

Formato para conversa normal:
{{
    "action": "normal_chat",
    "message": "resposta aqui"
}}

Formato para status:
{{
    "action": "server_status"
}}
"""

    return system_prompt + "\nUsuário: " + user_message


def ask_llm(prompt):
    response = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }
    )

    data = response.json()
    return data["response"]

def process_response(response):
    try:
        start = response.find("{")
        end = response.rfind("}") + 1

        json_str = response[start:end]
        return json.loads(json_str)

    except Exception:
        return {
            "action": "normal_chat",
            "message": response
        }

while True:
    user_input = input("Voce: ")

    if user_input.lower() == "sair":
        break

    # salvar memória manual
    if user_input.startswith("remember "):
        content = user_input.replace("remember ", "")

        try:
            key, value = content.split("=")
            update_memory(key.strip(), value.strip())
            print("Memoria salva.\n")
        except ValueError:
            print("Formato invalido. Use: remember chave=valor\n")

        continue

    prompt = build_prompt(user_input)
    raw_response = ask_llm(prompt)
    parsed = process_response(raw_response)

    action = parsed.get("action")

    if action == "server_status":
        raw_status = server_status()

        summary_prompt = f"""
Analise e resuma de forma objetiva o status abaixo do servidor:

{raw_status}
"""
        summary = ask_llm(summary_prompt)
        print("\nJarvis:", summary, "\n")
    
    if action == "docker_status":
        raw_status = docker_status()

        summary_prompt = f"""Analise e resuma de forma objetiva o status abaixo do docker:

{raw_status}
"""
        summary = ask_llm(summary_prompt)
        print("\nJarvis:", summary, "\n")

    elif action == "normal_chat":
    	message = parsed.get("message", "Sem resposta.")
    	print(f"\nJarvis: {message}\n")

    else:
        print("\nJarvis: Acao desconhecida.\n")
