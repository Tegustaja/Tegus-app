from dotenv import load_dotenv
from swarm import Swarm, Agent
from api_response import api_request

load_dotenv()
request = "Mis asi on heli laine ja kuida on sellega seotud Kaja Kallas"

# creating handoffs functions
def handoff_to_RAG():
    print("Handing off to RAG")
    return Rag_agent

def main_agent(request):
    print("Handing off to Math Agent")
    return api_request(request)

    

tunnihaldaja = Agent(
    name="Tunnihaldaja",
    instructions="Sina oled Tunnihaldaja ja sinu eesmärk on kindlaks määrata millise agendiga järgmisena rääkida",
    functions=[handoff_to_RAG]
)

Rag_agent = Agent(
    name="Rag agent",
    instructions="Sina vastad ainult selle põhjal, mida sulle on kontekstiks antud. Kui su käest küsitakse küsimus, mis on sinu kontekstist väljas, siis muuda see küsimus naljaks ja vasta selle naljaga",
    functions=[main_agent]
)

client = Swarm()


messages = [{"role": "user", "content": request}]
handoff_response = client.run(agent=tunnihaldaja, messages=messages)
print(handoff_response.messages[-1]["content"])