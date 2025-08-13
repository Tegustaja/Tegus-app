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

# Paths
CHROMA_PATH = "multiple_choise_db"
DATA_PATH = "data/multiple_choise"
FILE_GLOB = "multiplechoise.md"

def generate_data_store():
    documents = load_documents()
    chunks = split_lines(documents)
    save_to_chroma(chunks)

def load_documents():
    loader = DirectoryLoader(DATA_PATH, glob=FILE_GLOB)
    return loader.load()

def split_lines(documents):
    line_chunks = []
    for doc in documents:
        lines = doc.page_content.splitlines()
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                content = data.get("question", "")
                metadata = {k: v for k, v in data.items() if k != "question"}

                # Flatten the 'choices' dictionary into a string
                if "choices" in metadata:
                    metadata["choices"] = ", ".join([f"{key}: {value}" for key, value in metadata["choices"].items()])

                line_doc = Document(
                    page_content=content,
                    metadata={**doc.metadata, "line_index": i, **metadata}
                )
                line_chunks.append(line_doc)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON on line {i+1} of {doc.metadata.get('source')}: {e}")
                continue

    print(f"Split {len(documents)} documents into {len(line_chunks)} processed lines.")
    if line_chunks:
        print("Example processed line content:", line_chunks[0].page_content)
        print("Example processed line metadata:", line_chunks[0].metadata)
    return line_chunks

def save_to_chroma(chunks: list[Document]):
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    db = Chroma.from_documents(
        chunks,
        OpenAIEmbeddings(openai_api_key=my_api_key),
        persist_directory=CHROMA_PATH
    )
    db.persist()
    print(f"Saved {len(chunks)} processed lines to database in {CHROMA_PATH}.")

if __name__ == "__main__":
    generate_data_store()