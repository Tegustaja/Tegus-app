import os
from dotenv import load_dotenv, find_dotenv
import shutil
import nltk
nltk.download('punkt')  # Download the sentence tokenizer

from langchain_community.document_loaders.directory import DirectoryLoader
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

_ = load_dotenv(find_dotenv())  # read local .env file
my_api_key = os.environ['OPENAI_API_KEY']
CHROMA_PATH = "multiple_choise_db"
DATA_PATH = "data/multiple_choise"

def generate_data_store():
    documents = load_documents()
    chunks = split_lausete_jargi(documents)
    save_to_chroma(chunks)

def load_documents():
    loader = DirectoryLoader(DATA_PATH, glob="*.md")
    documents = loader.load()
    return documents

def split_lausete_jargi(documents):
    """Split documents into individual sentences."""
    sentence_chunks = []
    for doc in documents:
        # Split the document content into sentences
        sentences = nltk.sent_tokenize(doc.page_content)
        # Create a new Document object for each sentence, preserving metadata
        for i, sentence in enumerate(sentences):
            sentence_doc = Document(
                page_content=sentence.strip(),
                metadata={
                    **doc.metadata,
                    "sentence_index": i  # Optional: track sentence position
                }
            )
            sentence_chunks.append(sentence_doc)
    print(f"Split {len(documents)} documents into {len(sentence_chunks)} sentences.")
    if sentence_chunks:  # Print an example for debugging
        print("Example sentence:", sentence_chunks[0].page_content)
        print("Metadata:", sentence_chunks[0].metadata)
    return sentence_chunks

def save_to_chroma(chunks: list[Document]):
    # Clear out the database directory first
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
        
    # Create a vector database from the documents
    db = Chroma.from_documents(chunks, OpenAIEmbeddings(openai_api_key=my_api_key), persist_directory=CHROMA_PATH)
    db.persist()  # Saves the database to disk as a SQLite3 file
    print(f"Saved {len(chunks)} sentences to database in {CHROMA_PATH}.")

if __name__ == "__main__":
    generate_data_store()