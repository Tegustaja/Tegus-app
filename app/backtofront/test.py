from datetime import datetime
import json
from connect_db import get_data, insert_data

TABLE_NAME = "lesson_sessions"
ROW_ID = ""

def add_response(content: str):
    try:
        # Fetch existing responses
        responses_data = get_data(TABLE_NAME, "response", ROW_ID)

        # Handle failure
        if not isinstance(responses_data, list):
            return {
                'success': False,
                'error': f"Error fetching data: {responses_data}"
            }

        # Extract current responses list (or initialize empty list)
        row = responses_data[0] if responses_data else {}
        existing_responses = row.get("response", [])
        if not isinstance(existing_responses, list):
            existing_responses = []

        # Find the next id
        next_id = 1 if not existing_responses else max(resp["id"] for resp in existing_responses) + 1

        # Create the new response
        new_response = {
            "id": next_id,
            "timestamp": datetime.now().isoformat(),
            "content": content
        }

        # Append new response
        updated_responses = existing_responses + [new_response]

        # Write back to the same row, updating only the responses column
        insert_data(TABLE_NAME, {"response": updated_responses}, ROW_ID)

        return {
            'success': True,
            'message': f"Response added with id {next_id}",
            'response': new_response
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

#print(add_response(content="skjdfbgshfgskfbhsldgkj"))


def add_response(content: dict):
    try:
        # Step 1: Get current responses
        responses_data = get_data(TABLE_NAME, "response", ROW_ID)

        if not isinstance(responses_data, list):
            return {
                'success': False,
                'error': f"Error fetching responses: {responses_data}"
            }

        row = responses_data[0] if responses_data else {}
        existing_responses = row.get("response", [])
        if not isinstance(existing_responses, list):
            existing_responses = []

        # Step 2: Calculate next response ID
        next_id = 1 if not existing_responses else max(r["id"] for r in existing_responses) + 1

        # Step 3: Wrap the new content with id and timestamp
        new_response = {
            "id": next_id,
            "timestamp": datetime.now().isoformat(),
            "content": content  # content is already a dict like {"response": [...]}
        }

        # Step 4: Append and update
        updated_responses = existing_responses + [new_response]
        insert_data(TABLE_NAME, {"response": updated_responses}, ROW_ID)

        return {
            'success': True,
            'message': f"Response added with id {next_id}",
            'response': new_response
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }



print(add_response({"response":[
    """foilhesflksdfj"""
]}))