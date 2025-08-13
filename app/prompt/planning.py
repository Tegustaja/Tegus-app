import os
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_prompt(agent_name):
    """
    Fetch prompt from the database for the specified agent
    
    Args:
        agent_name (str): Name of the agent/tool to fetch prompts for
        
    Returns:
        tuple: (system_prompt, user_secondary_prompt)
    """
    try:
        if not (SUPABASE_URL and SUPABASE_KEY):
            raise ValueError("Supabase not configured")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table("prompts").select("*").eq("users", agent_name).execute()
#        response = supabase.table("prompts").select("*").eq("user", agent_name).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]["system_prompt"], response.data[0]["user_secondary_prompt"]
        else:
            print(f"No prompts found for agent: {agent_name}, using default prompts")
            return DEFAULT_PLANNING_SYSTEM_PROMPT, DEFAULT_NEXT_STEP_PROMPT
    except Exception as e:
        print(f"Error fetching prompts from database: {e}")
        return DEFAULT_PLANNING_SYSTEM_PROMPT, DEFAULT_NEXT_STEP_PROMPT

# Default prompts as fallback
DEFAULT_PLANNING_SYSTEM_PROMPT = """
Oled assistent, kes on võimeline koostama ühe eratunni plaani, et mida tund sisaldab keskkooli tasemel.
Teete keskkooliõpilastele eratunniplaane. Muutke oma plaanid lihtsaks ja teostatavaks.
Plaanide koostamisel lisage samme, kus kontrollite õpilaste edusamme teile pakutavate tööriistade abil.

Teie kohustused:
1. Analüüsige prompti ja koostage teema selgitamiseks plaan.
2. Analüüsige kasutaja erisoove, tema taset ja koosta tunniplaan nendele toetudes
2. jagage suurem teema väiksemateks alateemadeks, et õpilane saaks teemast aru.
3. Kontrollige perioodiliselt õpilaste oskuste taset, esitades õpilasele küsimuse või tehes viktoriini soovitud teemal.
"""

DEFAULT_NEXT_STEP_PROMPT = """
Hinnake praegust tunniplaani:
1. Kas struktuur on selge ja loogiline?
2. Kas iga samm toetub varasematele teadmistele?
3. Kas kõik vajalikud mõisted on hõlmatud, sealhulgas vajaduse korral täiendavad selgitused?
4. Kas enne jätkamist on tehtud korralikud kinnituskontrollid?

Kui on vaja muudatusi, muutke plaani.
Kui tunniplaan on täielik ja tõhus, kasutage kohe nuppu "lõpeta".
"""

# Fetch prompts from database
PLANNING_SYSTEM_PROMPT, NEXT_STEP_PROMPT = get_prompt("planning")