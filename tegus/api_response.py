import requests

def api_request(query):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }

    json_data = {
        'query': query,
        "X-API-Key": "rFmMp_d_G_-7SddAI_MyCYFjXIOnTwIKVn8gan5RV5U"
    }

    response = requests.post('http://app.rahudisain.ee:8888/rag-response', headers=headers, json=json_data)
    return response.json()

