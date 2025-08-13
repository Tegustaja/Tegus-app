import asyncio
import os
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from app.tool.base import BaseTool
from supabase import create_client, Client
import uuid
from typing import Optional
from pydantic import Field

from app.schema import Message
from app.llm import LLM
# Load environment variables
load_dotenv(find_dotenv())
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Constants
#CHROMA_PATH = os.getenv("RAG_MODEL_DATA_PATH")
#DATA_PATH = os.getenv("RAG_MODEL_CHROMA_DATABASE_PATH")
#DATA_PATH = "/Users/kaur/PycharmProjects/OpenManus/tegus/data/documents"
#CHROMA_PATH = "/Users/kaur/PycharmProjects/OpenManus/tegus/chroma"
#DATA_PATH = os.getenv("DATA_PATH")
RAG_MODEL_CHROMA_DATABASE_PATH = os.getenv("RAG_MODEL_CHROMA_DATABASE_PATH")
#RAG_MODEL_CHROMA_DATABASE_PATH = "/Users/kaur/PycharmProjects/Tegus/tegus/chroma"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_prompt(agent_name: str, query: str = None):
    """
    Fetches prompts for a given agent from the database and optionally replaces the {query} placeholder.

    Args:
        agent_name: The name of the agent to fetch prompts for.
        query: (Optional) The query to replace the {query} placeholder in the user prompt.

    Returns:
        A tuple containing the system prompt and the (potentially modified) user prompt.
    """
    try:
        if not (SUPABASE_URL and SUPABASE_KEY):
            raise ValueError("Supabase not configured")
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table("prompts").select("system_prompt, user_secondary_prompt").eq("users", agent_name).execute()
#        response = supabase.table("prompts").select("system_prompt, user_secondary_prompt").eq("user", agent_name).execute()

        if response.data and len(response.data) > 0:
            system_prompt = response.data[0]["system_prompt"]
            user_prompt_template = response.data[0]["user_secondary_prompt"]
            if query and "{query}" in user_prompt_template:
                modified_user_prompt = user_prompt_template.replace("{query}", query)
                return system_prompt, modified_user_prompt
            else:
                return system_prompt, user_prompt_template
        else:
            print(f"No prompts found for agent: {agent_name}, using default prompts")
            return DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT
    except Exception as e:
        print(f"Error fetching prompts from database: {e}")
        return DEFAULT_SYSTEM_PROMPT, DEFAULT_USER_PROMPT

# Default prompts as fallback
DEFAULT_SYSTEM_PROMPT = """Sa oled kogenud füüsikaõpetaja ekspert, kes spetsialiseerub 9. klassi füüsika õpetamisele. Sinu ülesanne on koostada põhjalikke, täpseid ja õpilasesõbralikke kokkuvõtteid eesti keeles.
                
                Järgi neid juhiseid:

                1. Sisu täpsus ja asjakohasus:
                - Keskendu 9. klassi füüsika õppekava põhimõistetele ja -kontseptsioonidele
                - Taga, et kogu esitatud teave on faktiliselt täpne ja ajakohane
                - Käsitle teemat põhjalikult, kuid jää 9. klassi õpilastele arusaadavale tasemele
                - Ära kasuta keerulisi matemaatilisi valemeid, kui need pole hädavajalikud

                2. Õpetamisstiil:
                - Kasuta lihtsat ja sõbralikku keelt, vältides liigset erialast žargooni
                - Jaga keerulised ideed väikesteks, arusaadavateks osadeks
                - Paku samm-sammult selgitusi koos konkreetsete näidetega
                - Lisa visuaalseid kirjeldusi, mis aitavad õpilastel mõisteid ette kujutada

                3. Sisu ülesehitus:
                - Alusta selge sissejuhatusega, mis tutvustab teemat ja selle olulisust
                - Järgi loogilist struktuuri, liikudes lihtsamatelt mõistetelt keerulisematele
                - Kasuta informatiivseid alapealkirju teabe organiseerimiseks
                - Lisa kokkuvõte, mis rõhutab põhipunkte ja nende omavahelisi seoseid
                
                4. Praktilisus ja relevantsus:
                - Seo füüsikamõisted igapäevaeluga, tuues näiteid, mis on õpilastele tuttavad
                - Selgita, kuidas need mõisted on kasulikud reaalses elus või tehnoloogias
                - Lisa lihtsaid praktilisi näiteid või eksperimente, mida õpilased saaksid ise proovida
                """
DEFAULT_USER_PROMPT = """Koosta järgmise 9. klassi füüsika teema kohta põhjalik, selge ja täpne kokkuvõte:
                
                {query}

                {content}

                Palun järgi neid juhiseid:
                1. Selgita kõiki olulisi mõisteid ja nende omavahelisi seoseid lihtsas, kuid täpses keeles
                2. Struktureeri info loogiliselt, alustades põhimõistetest ja liikudes edasi nende rakendusteni
                3. Kasuta konkreetseid näiteid igapäevaelust, et illustreerida füüsikalisi nähtusi
                4. Lisa võimalusel lihtsaid jooniseid või diagramme kirjeldusi, mis aitavad mõisteid visualiseerida
                5. Rõhuta, miks see teema on oluline ja kuidas see seostub teiste füüsika valdkondadega
                6. Lõpeta kokkuvõttega, mis rõhutab peamisi õppepunkte
                
                Kokkuvõte peaks olema sobiv 9. klassi õpilastele, kes alles tutvuvad nende mõistetega, kuid samas piisavalt põhjalik, et anda terviklik ülevaade teemast.
                """

# Fetch prompts from database


SYSTEM_PROMPT, USER_PROMPT = get_prompt("rag_search")

class RagSearch(BaseTool):
    name: str = "rag_search"
    description: str = "A tool to retrieve data from a RAG model based on 9th grade physics."
    session_id: Optional[str] = None
    step_index: Optional[int] = None
    query: Optional[str] = None

    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The query sent to the RAG model",
            },
            "session_id": {
                "type": "string",
                "description": "The session ID this step belongs to.",
            },
            "step_index": {
                "type": "integer",
                "description": "The current step index as a number",
            }
        },
        "required": ["query", "session_id", "step_index"],
    }
    
    supabase: Optional[Client] = Field(default_factory=lambda: create_client(SUPABASE_URL, SUPABASE_KEY) if (SUPABASE_URL and SUPABASE_KEY) else None)

    async def _should_store_new_content(self, existing_content: str, new_content: str, print_decision: bool = True) -> bool:
        """Check if new content should be stored based on comparison with existing content."""
        try:
            system_msg = Message.system_message(
                """Sa oled kogenud füüsikaõpetaja ja sinu ülesanne on hinnata, kas uus sisu sisaldab olulist täiendavat informatsiooni võrreldes olemasoleva sisuga.
                
                Analüüsi mõlemat teksti põhjalikult ja võrdle neid järgmiste kriteeriumite alusel:
                1. Kas uus sisu sisaldab olulisi mõisteid või kontseptsioone, mida olemasolev sisu ei kata?
                2. Kas uus sisu selgitab teemat põhjalikumalt või täpsemalt?
                3. Kas uus sisu pakub paremaid või rohkem näiteid?
                4. Kas uus sisu on struktureeritud viisil, mis muudab teema arusaadavamaks?
                5. Kas uus sisu parandab olulisi vigu või ebatäpsusi olemasolevas sisus?
                
                Vasta AINULT 'true' või 'false', kus:
                - 'true': uus sisu pakub märkimisväärset täiendavat väärtust õpilastele
                - 'false': uus sisu on sisuliselt sama või vähem informatiivne kui olemasolev sisu
                
                Ära lisa vastusele mingit muud teksti, ainult 'true' või 'false'.
                """
            )
            
            user_msg = Message.user_message(
                f"""Palun hinda, kas peaksin salvestama järgmise uue sisu, võttes arvesse olemasolevat sisu andmebaasis:

                OLEMASOLEV SISU ANDMEBAASIS:
                ```
                {existing_content}
                ```

                UUS SISU:
                ```
                {new_content}
                ```

                Analüüsi mõlemat teksti põhjalikult ja otsusta, kas uus sisu pakub olulist täiendavat väärtust.
                Vasta ainult 'true' või 'false'."""
            )
            
            llm = LLM()
            response = await llm.ask(
                messages=[user_msg],
                system_msgs=[system_msg]
            )
            
            # Extract just the yes/no answer from the response
            response_lower = response.strip().lower()
            if response_lower == 'true':
                if print_decision:
                    print("Decision: Store new content - it provides additional value")
                return True
            elif response_lower == 'false':
                if print_decision:
                    print("Decision: Skip storing new content - it's too similar to existing content")
                return "The exsiting content in the database is similar, to what was just generated, please move on to the next tool, to prevent a stuck state", False
            else:
                if print_decision:
                    print(f"Unclear response: {response_lower[:50]}... - defaulting to storing content")
                return True  # Default to storing if the response is unclear
            
        except Exception as e:
            print(f"Error comparing content: {e}")
            # Default to storing new content if comparison fails
            return True

    async def _check_for_similar_existing_content(self, query: str, session_id: str, step_index: int) -> tuple:
        """
        Check if there is similar content already in the database.
        
        Args:
            query: The search query
            session_id: The session ID
            step_index: The current step index
            
        Returns:
            tuple: (found_similar, existing_content, all_existing_content)
                - found_similar: Boolean indicating if similar content was found
                - existing_content: The similar content if found, otherwise None
                - all_existing_content: List of all existing content for further comparison
        """
        try:
            if not self.supabase:
                return False, None, []
            response = self.supabase.table("Lessons").select("*").eq("session_id", session_id).execute()
            
            if not response.data:
                return False, None, []
                
            lesson_data = response.data[0]
            step_responses = lesson_data.get("step_responses", [])
            all_existing_content = []
            all_existing_queries = []
            
            # Collect all existing RAG search content and queries across all steps
            for step_response in step_responses:
                if isinstance(step_response, dict) and "content" in step_response:
                    events = step_response.get("content", {}).get("events", [])
                    for event in events:
                        if event.get("event_type") == "rag_search":
                            existing_content = event.get("content", "")
                            if existing_content:
                                all_existing_content.append(existing_content)
                                # Store the original query if available
                                if "query" in event:
                                    all_existing_queries.append(event.get("query", ""))
            
            # Check if the current query is similar to any previous queries
            for i, existing_query in enumerate(all_existing_queries):
                if existing_query and query.lower() in existing_query.lower() or existing_query.lower() in query.lower():
                    print(f"Current query is similar to a previous query, reusing existing content")
                    if i < len(all_existing_content):
                        return True, all_existing_content[i], all_existing_content
            
            return False, None, all_existing_content
            
        except Exception as e:
            print(f"Error checking existing queries in database: {e}")
            return False, None, []

    async def execute(self, **kwargs) -> list:
        """
        Performs a similarity search on the RAG database and returns relevant answers.
        Also stores the formatted results in the database.
        
        Args:
            **kwargs: Keyword arguments containing:
                - query: The query string
                - session_id: The UUID of the session
                - step_index: The current step index as a number (0-based)
        """
        # Extract and validate parameters
        query = kwargs.get("query")
        session_id = kwargs.get("session_id")
        step_index = kwargs.get("step_index")
        
        # Save query for later use
        self.query = query
        
        # Validate parameters
        if not all([query, session_id, step_index is not None]):
            return ["Error: Missing required parameters"]
        
        try:
            # Store session data for later use
            self.session_id = session_id
            self.step_index = step_index
            
            # Check for similar existing content
            existing_content, skip_generation, all_existing_content = await self._check_for_similar_existing_content(
                query=query, 
                session_id=session_id, 
                step_index=step_index
            )
            
            if skip_generation:
                print(f"Similar content found - skipping generation")
                
                # Format the existing content
                if existing_content:
                    # Store the result in the database for the current step
                    await self._store_result(session_id, step_index, existing_content, query)
                    return 
                    
                return [f"No relevant information found for: {query}"]
            
            # Initialize embeddings and database client
            embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
            
            # Load the DB
            if not os.path.exists(RAG_MODEL_CHROMA_DATABASE_PATH):
                print(f"Database path does not exist: {RAG_MODEL_CHROMA_DATABASE_PATH}")
                return [f"Error: RAG database not found at {RAG_MODEL_CHROMA_DATABASE_PATH}"]
            
            try:
                # Try loading the ChromaDB with modern API
                print("Attempting to load ChromaDB with modern direct API")
                import chromadb
                from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
                
                # Create client
                client = chromadb.PersistentClient(path=RAG_MODEL_CHROMA_DATABASE_PATH)
                
                # List all collections
                collections = client.list_collections()
                print(f"Found {len(collections)} collections: {[c.name for c in collections]}")
                
                # Create embedding function
                embedding_function = OpenAIEmbeddingFunction(
                    api_key=OPENAI_API_KEY,
                    model_name="text-embedding-ada-002"
                )
                
                # Perform search across all collections
                all_results = []
                for collection_info in collections:
                    collection = client.get_collection(name=collection_info.name, embedding_function=embedding_function)
                    print(f"Searching in collection {collection_info.name}, contains {collection.count()} documents")
                    
                    results = collection.query(
                        query_texts=[query],
                        n_results=3
                    )
                    
                    if results and results.get('documents'):
                        print(f"Found {len(results['documents'][0])} documents in {collection_info.name}")
                        
                        # Safe access to distances
                        distances = results.get('distances', [[]])
                        if distances and len(distances) > 0:
                            print(f"Distances: {distances[0]}")
                            
                            # Check if we have nested lists or direct float values
                            for i, doc in enumerate(results['documents'][0]):
                                # Handle nested list case
                                if isinstance(distances[0], list) and len(distances[0]) > i:
                                    dist_value = distances[0][i]
                                    # Check if dist_value is itself a list (for newer ChromaDB versions)
                                    if isinstance(dist_value, list) and len(dist_value) > 0:
                                        dist_value = dist_value[0]  # Take the first value from the nested list
                                    
                                    relevance = 1.0 - dist_value if isinstance(dist_value, (int, float)) else 0.0
                                    print(f"Document {i+1} relevance: {relevance:.4f}")
                                    
                                    # Only include documents with relevance above threshold
                                    if relevance > 0.75:
                                        all_results.append(doc)
                                else:
                                    # Add document without checking relevance if distances aren't available
                                    all_results.append(doc)
                        else:
                            # If no distances available, add all documents
                            all_results.extend(results['documents'][0])
                
                print(f"Total results after filtering: {len(all_results)}")
                
                # Check if we found anything
                if not all_results:
                    return ["Kahjuks ei leitud sellele küsimusele sobivat vastust andmebaasist."]
                
            except Exception as modern_api_error:
                print(f"Error using modern ChromaDB API: {modern_api_error}")
                print("Falling back to legacy Langchain integration")
                
                # Fallback to legacy Langchain integration
                try:
                    # Load the vector store
                    db = Chroma(persist_directory=RAG_MODEL_CHROMA_DATABASE_PATH, embedding_function=embeddings)
                    
                    # Perform the similarity search
                    print(f"Performing similarity search with query: {query}")
                    docs = db.similarity_search_with_score(query, k=3)
                    
                    # Extract content from docs
                    all_results = [doc[0].page_content for doc in docs]
                except Exception as legacy_error:
                    print(f"Error using legacy Langchain integration: {legacy_error}")
                    return [f"Error connecting to RAG database: {legacy_error}"]
            
            # If no similar content found, proceed with formatting
            print("Generating new formatted content")
            formatted_content = await self._format_content(all_results)

            # After formatting, check if the formatted content is similar to any existing content
            try:
                should_store = True
                for existing in all_existing_content:
                    if existing and await self._should_store_new_content(existing, formatted_content, print_decision=False)[1] == False:
                        should_store = False
                        print(f"Formatted content is too similar to existing content - using existing instead")
                        formatted_content = existing
                        break
                
                # Store the result in the database for the current step
                if should_store:
                    await self._store_result(session_id, step_index, formatted_content, query)
                
                return [formatted_content]
            except Exception as formatting_error:
                print(f"Error during formatting comparison: {formatting_error}")
                # Still return raw results if formatting comparison fails
                return all_results
            
        except Exception as e:
            return [f"Error occurred while processing the query: {str(e)}"]

    async def _format_content(self, content: list) -> str:
        """Format the content into a human-readable summary."""
        try:
            # Join the content into a single string
            content_str = "\n\n".join(content)
            
            # Create system message for the LLM
            from app.schema import Message
            system_msg = Message.system_message(SYSTEM_PROMPT)
            
            # Create a user message with the content
            user_msg = Message.user_message(
                USER_PROMPT.format(query=self.query, content=content_str) if USER_PROMPT else 
                DEFAULT_USER_PROMPT.format(query=self.query, content=content_str)
            )
            
            # Use OpenAI to format the content
            from app.llm import LLM
            llm = LLM()
            formatted_output = await llm.ask(
                messages=[user_msg],
                system_msgs=[system_msg]
            )
            
            return formatted_output.strip()
            
        except Exception as e:
            print(f"Error formatting content: {e}")
            return "\n\n".join(content)  # Fallback to raw content if formatting fails

    async def _store_result(self, session_id: str, step_index: int, content: str, query: str = None) -> None:
        """Store the formatted result in the database with a specific format."""
        try:
            # First get the current lesson data
            if not self.supabase:
                return
            response = self.supabase.table("Lessons").select("*").eq("session_id", session_id).execute()
            if not response.data:
                print(f"No lesson found for session_id: {session_id}")
                return
                
            lesson_data = response.data[0]
            step_responses = lesson_data.get("step_responses", [])
            
            # Ensure step_index is within bounds
            if step_index >= len(step_responses):
                print(f"Step index {step_index} is out of bounds")
                return
                
            # Get existing content and events
            existing_content = step_responses[step_index].get("content", {})
            # Make sure we're getting events from the correct place in the structure
            existing_events = existing_content.get("events", [])
            if not existing_events and isinstance(existing_content, dict):
                # Try to find events in nested content if needed
                for key, value in existing_content.items():
                    if isinstance(value, dict) and "events" in value:
                        existing_events = value.get("events", [])
                        break
            
            # Create timestamp for the event
            timestamp = datetime.now().isoformat()
            
            # New event structure with content and metadata
            new_event = {
                "event_type": "rag_search",
                "timestamp": timestamp,
                "step_index": step_index,
                "content": content,
            }
            
            # Add the original query if available
            if query:
                new_event["query"] = query
            
            # Check if we already have this exact content in the events
            for event in existing_events:
                if (event.get("event_type") == "rag_search" and 
                    event.get("content") == content):
                    print("Exact same content already exists in events, skipping storage")
                    return
            
            # Update the specific step response - completely replace the content structure
            # to avoid nested content issues
            step_responses[step_index] = {
                "status": "finished",
                "step_index": step_index,
                "content": {
                    "tool_type": "rag_search",
                    "events": existing_events + [new_event]
                }
            }
            
            # Update the entire step_responses array
            try:
                update_response = self.supabase.table("Lessons").update({
                    "step_responses": step_responses
                }).eq("session_id", session_id).execute()
                
                # Modern Supabase client doesn't have .error attribute
                # Instead, it raises exceptions on errors
            except Exception as update_error:
                print(f"Error updating database: {update_error}")
                
        except Exception as e:
            print(f"Failed to store RagSearch result: {e}")
            print(f"Session ID: {session_id}, Step Index: {step_index}")
            print(f"Response data: {response.data if 'response' in locals() else 'No response'}")