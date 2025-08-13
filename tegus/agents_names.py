from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import os
from answering import answering

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

_ = load_dotenv(find_dotenv())
my_api_key = os.environ['OPENAI_API_KEY']
CHROMA_PATH = "chroma"
RAG_PROMPT_TEMPLATE = """
Answer the question using only the following context:
{context}
-------------------------------------------------------------
Answer this question based on the context above: {question} 
"""
MATH_AGENT_PROMPT = """
Create a suitable physics problem based on the context below:
{context}
-------------------------------------------------------------
Create a suitable physics problem based on the context above: {question} Answer in less than 50 words"""

DATA_PATH = "data/documents"
load_dotenv()


def chat_query(prompt):
    client = OpenAI(my_api_key)
    completion = client.chat.completions.create(
       model="gpt-3.5-turbo",
        messages=[
            {"role": "developer", "content": ''},
       ]
    )
    return completion.choices[0].message


def rag_agent(query_text, prompti_templiit):
    # prepare the db
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # search the db for the relevant chunks -> returns a list of (document, score) tuples
    results = db.similarity_search_with_relevance_scores(query_text, k=5)  # k is the number of results to return
    if len(results) == 0 or results[0][1] < 0.7:  # if the relevance score of the first result is less than 0.7, return
        return f"Unable to find matching results for '{query_text}'"
    # create the prompt for the chatbot
    context = "\n\n---\n\n".join([doc.page_content for doc, score in results])
    prompt_template = ChatPromptTemplate.from_template(prompti_templiit)
    prompt = prompt_template.format(context=context, question=query_text)
    
    # the LLM uses the prompt to answer the question
    model = ChatOpenAI()
    response_text = model.predict(prompt)
 
    # Get sources of the matching documents
    #sources = [doc.metadata.get("source", None) for doc, _score in results]
    
    # Format and return response including generated text and sources
    #formatted_response = f"Response: {response_text}\nSources: {sources}"
    return response_text

# Let's call our function we have defined
#formatted_response, response_text = query_rag(query_text)
# and finally, inspect our final response!
#print(response_text)
    #return results
    #with open("logifail.txt", "w") as lg:
    #    lg.write(f"{datetime.now}||Query: {prompt} ||Response: {formatted_response}")
    #return jsonify({"query": query_text, "context" : context, "response": formatted_response})


question = 'Kas sa saad teha mulle ühe ülesande kahe jadamisi ühendatud takisti kohta'

def math_agent():
    return rag_agent(question, MATH_AGENT_PROMPT)


if answering(question)[0] == 'Mati.':
    print('--------------------------------------------------')
    print('Mati is responding to this question:')
    print(rag_agent(question, RAG_PROMPT_TEMPLATE))
else:
    print('---------------------------------------------------')
    print('Anna is responding to this question:')
    print(math_agent())