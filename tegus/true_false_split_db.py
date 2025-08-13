import os
from dotenv import load_dotenv, find_dotenv
import shutil
import json

from langchain_community.document_loaders.directory import DirectoryLoader
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Load environment variables
_ = load_dotenv(find_dotenv())
my_api_key = os.environ['OPENAI_API_KEY']

# Paths for this new database
CHROMA_PATH_TF = "truefalse_db"
DATA_PATH_TF = "data/truefalse"  # Make sure this directory exists and contains your .md file
FILE_GLOB_TF = "true_false.md"       # Adjust the filename if needed

def generate_true_false_data_store():
    documents = load_true_false_documents()
    chunks = split_true_false_lines(documents)
    save_to_true_false_chroma(chunks)

def load_true_false_documents():
    loader = DirectoryLoader(DATA_PATH_TF, glob=FILE_GLOB_TF)
    return loader.load()

def split_true_false_lines(documents):
    """Split documents into individual lines and parse them as JSON for true/false questions."""
    line_chunks = []
    for doc in documents:
        lines = doc.page_content.splitlines()
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                content = data.get("question", "")  # Use the question as the content
                metadata = {k: v for k, v in data.items() if k != "question"} # Store other fields as metadata
                line_doc = Document(
                    page_content=content,
                    metadata={**doc.metadata, "line_index": i, **metadata}
                )
                line_chunks.append(line_doc)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON on line {i+1} of {doc.metadata.get('source')}: {e}")
                continue

    print(f"Split {len(documents)} documents into {len(line_chunks)} processed lines for true/false questions.")
    if line_chunks:
        print("Example processed line content (TF):", line_chunks[0].page_content)
        print("Example processed line metadata (TF):", line_chunks[0].metadata)
    return line_chunks

def save_to_true_false_chroma(chunks: list[Document]):
    # Clear existing DB for true/false questions
    if os.path.exists(CHROMA_PATH_TF):
        shutil.rmtree(CHROMA_PATH_TF)

    # Create vector DB for true/false questions
    db = Chroma.from_documents(
        chunks,
        OpenAIEmbeddings(openai_api_key=my_api_key),
        persist_directory=CHROMA_PATH_TF
    )
    db.persist()
    print(f"Saved {len(chunks)} processed lines to database in {CHROMA_PATH_TF}.")

if __name__ == "__main__":
    generate_true_false_data_store()