"""
Centralized prompt service for fetching prompts from the database.
This service provides a unified interface for all prompt-related operations.
"""

import os
from typing import Optional, Tuple
from supabase import create_client, Client
from app.logger import logger

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class PromptService:
    """Service for managing and fetching prompts from the database."""
    
    def __init__(self):
        """Initialize the prompt service."""
        if not (SUPABASE_URL and SUPABASE_KEY):
            raise ValueError("Supabase not configured")
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    async def get_prompt(self, prompt_name: str) -> Tuple[str, str]:
        """
        Fetch a prompt from the database by name.
        
        Args:
            prompt_name: The name of the prompt to fetch
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        try:
            response = self.supabase.table("prompts").select("system_prompt, user_prompt").eq("name", prompt_name).execute()
            
            if response.data and len(response.data) > 0:
                prompt_data = response.data[0]
                system_prompt = prompt_data.get("system_prompt", "")
                user_prompt = prompt_data.get("user_prompt", "")
                
                logger.info(f"Successfully fetched prompt: {prompt_name}")
                return system_prompt, user_prompt
            else:
                logger.warning(f"No prompt found for name: {prompt_name}")
                return "", ""
                
        except Exception as e:
            logger.error(f"Error fetching prompt {prompt_name}: {str(e)}")
            return "", ""
    
    async def get_combined_prompt(self, prompt_name: str) -> str:
        """
        Fetch a prompt and combine system and user prompts.
        
        Args:
            prompt_name: The name of the prompt to fetch
            
        Returns:
            Combined prompt string
        """
        system_prompt, user_prompt = await self.get_prompt(prompt_name)
        
        if system_prompt and user_prompt:
            return f"{system_prompt}\n\n{user_prompt}"
        elif system_prompt:
            return system_prompt
        elif user_prompt:
            return user_prompt
        else:
            return ""
    
    async def get_system_prompt(self, prompt_name: str) -> str:
        """
        Fetch only the system prompt.
        
        Args:
            prompt_name: The name of the prompt to fetch
            
        Returns:
            System prompt string
        """
        system_prompt, _ = await self.get_prompt(prompt_name)
        return system_prompt
    
    async def get_user_prompt(self, prompt_name: str) -> str:
        """
        Fetch only the user prompt.
        
        Args:
            prompt_name: The name of the prompt to fetch
            
        Returns:
            User prompt string
        """
        _, user_prompt = await self.get_prompt(prompt_name)
        return user_prompt
    
    async def list_available_prompts(self) -> list:
        """
        List all available prompt names in the database.
        
        Returns:
            List of prompt names
        """
        try:
            response = self.supabase.table("prompts").select("name, description, category").execute()
            
            if response.data:
                return response.data
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error listing prompts: {str(e)}")
            return []

# Global instance - lazy initialized
_prompt_service_instance = None

def get_prompt_service() -> PromptService:
    """Get or create the global prompt service instance."""
    global _prompt_service_instance
    if _prompt_service_instance is None:
        _prompt_service_instance = PromptService()
    return _prompt_service_instance

# Convenience functions for backward compatibility
async def get_prompt(prompt_name: str) -> Tuple[str, str]:
    """Backward compatibility function."""
    service = get_prompt_service()
    return await service.get_prompt(prompt_name)

async def get_combined_prompt(prompt_name: str) -> str:
    """Backward compatibility function."""
    service = get_prompt_service()
    return await service.get_combined_prompt(prompt_name)
