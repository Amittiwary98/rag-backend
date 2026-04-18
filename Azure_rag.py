from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient    
from azure.search.documents.indexes.models import SearchIndex, SimpleField, SearchableField
from fastapi import FastAPI, File, UploadFile   
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv
import os
import uuid

load_dotenv()


#####azure openai client setup#####
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_key = os.getenv("AZURE_OPENAI_KEY")
azureopenai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-12-01-preview",
)

###connection to azure search service###
search_client=SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY"))
)
##embeddings generation function##
def getembeddings(text):
    response = azureopenai_client.embeddings.create(
        input=text,
        model="embed-model"

    )
    return response.data[0].embedding   

####chunking of data and upload to azure search index##

def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

##ingestion of data into azure search index##
def upload_data(chunks, filename):
    docs = []
    for text in chunks:
        docs.append({
            "id":str(uuid.uuid4()),
            "content": text,
            "filename":filename,
        "embedding":getembeddings(text)
    })
    search_client.upload_documents(documents=docs)


def chat(query):
    query_embedding=getembeddings(query)
    vector_query = VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=5,
        fields="embedding"
    )


    results=search_client.search(
        search_text=query,
        vector_queries=[vector_query],
        )
    
    context=""
 
    for result in results:
      print("RESULT:", result)   # for checking the structure of the result

      content = result.get("content") or result.get("text") or result.get("chunk")
      print("CONTENT:", content)   # for checking the retrieved content
      if content:
        context += content + " "
    print("CONTEXT:", context)   # for checking the retrieved context
    print("QUERY:", query)   # for checking the input query
    response = azureopenai_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a helpful assistant. if the answer is not relevant  to the question, say you don't know."},
            {"role": "user", "content": f"Answer the question based on the following context: {context} Question: {query}"}
        ],
        model="chat-model"
    )
    return response.choices[0].message.content

