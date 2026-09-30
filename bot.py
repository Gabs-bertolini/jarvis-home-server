import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
import discord
from discord import app_commands
from requests.exceptions import RequestException, Timeout
from memory import load_memory, update_memory
from actions import server_status, docker_status

load_dotenv()

# Configurações do seu ambiente
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://192.168.0.211:11434")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN") # O Token que fica na aba "Bot" do painel

# Inicialização do Bot do Discord com Intents básicas
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --- SUAS FUNÇÕES ORIGINAIS DO JARVIS (MANTIDAS EXATAMENTE IGUAIS) ---
def build_prompt(user_message: str) -> str:
    memory = load_memory()
    system_prompt = f"""Você é Jarvis, meu assistente pessoal de infraestrutura.
Memória persistente do usuário:
{json.dumps(memory, indent=4, ensure_ascii=False)}
Você possui ações disponíveis (- normal_chat, - server_status, - docker_status).
REGRAS: Responda SEMPRE em JSON válido. Nunca escreva texto fora do JSON.
Formato para conversa normal: {{"action": "normal_chat", "message": "resposta aqui"}}
Formato para status: {{"action": "server_status"}}"""
    return system_prompt + "\nUsuário: " + user_message

def ask_llm(prompt: str) -> str:
    try:
        response = requests.post(f"{OLLAMA_HOST}/api/generate", json={"model": MODEL, "prompt": prompt, "stream": False}, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception:
        return '{"action": "normal_chat", "message": "Erro ao conectar à IA."}'

def process_response(response: str) -> dict:
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        return json.loads(response[start:end])
    except Exception:
        return {"action": "normal_chat", "message": response}

def _process_chat_message(message: str) -> str:
    prompt = build_prompt(message)
    raw_response = ask_llm(prompt)
    parsed = process_response(raw_response)
    action = parsed.get("action")

    if action == "server_status":
        raw_status = server_status()
        summary = ask_llm(f"Analise e resuma de forma objetiva o status abaixo do servidor:\n{raw_status}")
        return summary if summary else "Não consegui gerar o resumo do servidor."
    elif action == "docker_status":
        raw_status = docker_status()
        summary = ask_llm(f"Analise e resuma de forma objetiva o status abaixo do docker:\n{raw_status}")
        return summary if summary else "Não consegui gerar o resumo do Docker."
    
    return parsed.get("message", "Sem resposta.")

# --- COMANDO DO DISCORD COM TRATAMENTO DE TIMEOUT (DEFER) ---
@tree.command(name="chat", description="Fale com o Jarvis, seu assistente pessoal de infraestrutura")
async def chat_command(interaction: discord.Interaction, mensagem: str):
    # PASSO CHAVE: Diz ao Discord para exibir "Jarvis está pensando..." e estender o tempo para 15 minutos
    await interaction.response.defer()
    
    try:
        # Envia para a sua LLM local processar (pode demorar o quanto precisar)
        resposta_jarvis = _process_chat_message(mensagem)
        
        # Envia a resposta final de volta para o chat do Discord
        await interaction.followup.send(resposta_jarvis)
    except Exception as e:
        await interaction.followup.send(f"Ocorreu um erro ao processar sua mensagem: {str(e)}")

# Evento de inicialização do Bot
@client.event
async def on_ready():
    # Sincroniza os comandos com o Discord assim que liga
    await tree.sync()
    print(f"🚀 {client.user} está online e pronto no servidor!")

# Inicia o Bot persistente
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Erro: A variável DISCORD_BOT_TOKEN não foi configurada no seu .env")
    else:
        client.run(BOT_TOKEN)
