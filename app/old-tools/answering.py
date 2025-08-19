import os
from dotenv import load_dotenv, find_dotenv
import argparse
#import gradio as gr
from datetime import datetime
from flask import jsonify
import asyncio
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

#from create_database import load_documents, split_lausete_jargi, split_text

_ = load_dotenv(find_dotenv())
my_api_key = os.environ['OPENAI_API_KEY']
CHROMA_PATH = "kusimused_db"
PROMPT_TEMPLATE = """
Answer the question using only the following context:
{context}
-------------------------------------------------------------
Answer this question based on the context above: {question} 
"""
DATA_PATH = "data/kusimused"


async def answering(query_text):
    # prepare the db
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # search the db for the relevant chunks -> returns a list of (document, score) tuples
    results = db.similarity_search_with_relevance_scores(query_text, k=5)  # k is the number of results to return
    if len(results) == 0 or results[0][1] < 0.7:  # if the relevance score of the first result is less than 0.7, return
        return f"Unable to find matching results for '{query_text}'"
    
    #print(results[0][0].page_content)
    content = []
    count = 0
    while True:
        try:
            content.append(results[0][count].page_content)
            count += 1
        except:
            break
    

    answering = []
    for i in content:
        answering.append(i.split()[-1])
    
    return answering


