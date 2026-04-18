import os

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from Azure_rag import chat, upload_data, chunk_text

class ChatMessage(BaseModel):
    question: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from pypdf import PdfReader

@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    print(file.filename)
    ext = os.path.splitext(file.filename)[1].lower()
    print(ext)
    if ext == ".pdf":
        reader=PdfReader(file.file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    else:
        with open("uploaded_file", "wb") as f:
         f.write(file.file.read())   

        with open("uploaded_file", "r", encoding="utf-8") as f:
          text = f.read()
    
    chunks = chunk_text(text)
    upload_data(chunks, file.filename)   

    return {"message": "File uploaded successfully"}


@app.post("/chat")
def chat_endpoint(req: ChatMessage):
    response = process_chat(req)
    return {"answer": response}

@app.get("/")
def hello():
    return {'status':'app is running'}

def process_chat(req):
    response = chat(req.question)  
    return response