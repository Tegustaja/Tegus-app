import os
from dotenv import load_dotenv, find_dotenv
import shutil

from langchain_community.document_loaders.directory import DirectoryLoader
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Load environment variables
_ = load_dotenv(find_dotenv())
my_api_key = os.environ['OPENAI_API_KEY']

# Paths
CHROMA_PATH = "calculation_db"
DATA_PATH = "data/calculation_db"
FILE_GLOB = "calculation.md"

def generate_data_store():
    documents = load_documents()
    chunks = split_lines(documents)
    save_to_chroma(chunks)

def load_documents():
    # Load only the specified markdown file
    loader = DirectoryLoader(DATA_PATH, glob=FILE_GLOB)
    return loader.load()

def split_lines(documents):
    """Split documents into individual lines."""
    line_chunks = []
    for doc in documents:
        lines = doc.page_content.splitlines()
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            line_doc = Document(
                page_content=line,
                metadata={**doc.metadata, "line_index": i}
            )
            line_chunks.append(line_doc)
    print(f"Split {len(documents)} documents into {len(line_chunks)} lines.")
    if line_chunks:
        print("Example line:", line_chunks[0].page_content)
        print("Metadata:", line_chunks[0].metadata)
    return line_chunks

def save_to_chroma(chunks: list[Document]):
    # Clear existing DB
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # Create vector DB
    db = Chroma.from_documents(
        chunks,
        OpenAIEmbeddings(openai_api_key=my_api_key),
        persist_directory=CHROMA_PATH
    )
    db.persist()
    print(f"Saved {len(chunks)} lines to database in {CHROMA_PATH}.")

if __name__ == "__main__":
    generate_data_store()
