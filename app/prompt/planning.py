import asyncio
from app.services.prompt_service import get_prompt_service

async def get_prompt(agent_name):
    """
    Fetch prompt from the database for the specified agent
    
    Args:
        agent_name (str): Name of the agent/tool to fetch prompts for
        
    Returns:
        tuple: (system_prompt, user_secondary_prompt)
    """
    try:
        prompt_service = get_prompt_service()
        system_prompt, user_prompt = await prompt_service.get_prompt(agent_name)
        
        if system_prompt and user_prompt:
            return system_prompt, user_prompt
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

# Initialize with default prompts - will be updated when get_prompt is called
PLANNING_SYSTEM_PROMPT = DEFAULT_PLANNING_SYSTEM_PROMPT
NEXT_STEP_PROMPT = DEFAULT_NEXT_STEP_PROMPT

async def initialize_prompts():
    """Initialize prompts from database - call this when needed"""
    global PLANNING_SYSTEM_PROMPT, NEXT_STEP_PROMPT
    try:
        system_prompt, user_prompt = await get_prompt("planning")
        if system_prompt and user_prompt:
            PLANNING_SYSTEM_PROMPT = system_prompt
            NEXT_STEP_PROMPT = user_prompt
    except Exception as e:
        print(f"Error initializing prompts: {e}")
        # Keep default prompts