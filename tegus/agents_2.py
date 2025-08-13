from dotenv import load_dotenv
import os
import requests
import json
from answering import chatbot_response

load_dotenv()
query = "Mida tähendab Newtoni esimene seadus?"

API_KEY = os.getenv("OPENAI_API_KEY")
API_URL = "https://api.openai.com/v1/chat/completions"

def chat_with_gpt(prompt, json_file="customer_info.json"):
    with open(json_file, "r", encoding="utf-8") as file:
        json_content = json.dumps(json.load(file), indent=2)

    full_prompt = f"""{prompt}\n\nHere is the JSON data:\n{json_content}
                    Return only one name, the one who acts next. Never return a response, here are your options on who should act next:
                     "Kalle" - RAG model agent, who knows more about the topic than you
                     Always return a name from the list, otherwise return "None" """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.7
    }
    
    response = requests.post(API_URL, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]



if chat_with_gpt(query) == "Kalle":
    print(chatbot_response(query_text=query))
else:
    print("Kahjuks pole sellele küsimusele head vastust")



