import requests
from memory import load_memory, update_memory


MODEL = "llama3.2:3b"  # troque pelo seu modelo


def build_prompt(user_message):
    memory = load_memory()

    system_prompt = f"""
Você é Jarvis, assistente pessoal de infraestrutura.

Memória persistente do usuário:
{memory}

Use essas informações para responder melhor.
"""

    return system_prompt + "\nUsuário: " + user_message


def ask_llm(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        }
    )

    data = response.json()
    return data["response"]


while True:
    user_input = input("Voce: ")

    if user_input.lower() == "sair":
        break

    if user_input.startswith("remember "):
        content = user_input.replace("remember ", "")
        key, value = content.split("=")

        update_memory(key.strip(), value.strip())
        print("Memória salva.\n")
        continue

    prompt = build_prompt(user_input)
    response = ask_llm(prompt)

    print("\nJarvis:", response, "\n")
