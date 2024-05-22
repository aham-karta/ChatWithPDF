from flask import Flask, request
from flask_cors import CORS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from langchain_community.embeddings import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import torch
from groq import Groq
from dotenv import load_dotenv
import os
load_dotenv()
app = Flask(__name__)
CORS(app) 

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    query = data.get('query')
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=20,
        separators=["\n\n", "\n", " ", ""],
    )
    reader = PdfReader("pdf1.pdf")
    pages=len(reader.pages)
    document_data=""
    for i in range(pages):
        document_data+=" "+reader.pages[i].extract_text()
    texts = text_splitter.create_documents([document_data])
    texts2=[]
    for i in texts:
        texts2.append(i.page_content)
    print(texts2)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    doc_result = embeddings.embed_documents(texts2)
    vectors = []
    for i in range(len(doc_result)):
        vectors.append(
            {
                "id": f"vec{i+1}", 
                "values": doc_result[i], 
                "metadata": {'text': texts2[i]}
            }
        )
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    pc.create_index(
        name="quickstart",
        dimension=384, 
        metric="euclidean",
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        ) 
    )
    index = pc.Index("quickstart")
    index.upsert(
        vectors=vectors,
        namespace= "ns1"

    )
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device=device)
    xq = model.encode(query).tolist()
    xc=index.query(
        namespace="ns1",
        vector=xq,
        top_k=10,
        include_values=True,
        include_metadata=True
    )
    relevant_chunk=""
    for result in xc['matches']:
        relevant_chunk+=" "+result['metadata']['text']
    print(relevant_chunk)
    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {
                "role": "system",
                "content": f"answer EXACTLY based on [{relevant_chunk}] - try to use the same words"
            },
            {
                "role": "user",
                "content": query
            }
        ],
        temperature=0,
        max_tokens=8192,
        top_p=1,
        stream=True,
        stop=None,
    )
    relevant_response=""
    for chunk in completion:
        relevant_response+=chunk.choices[0].delta.content or ""
    pc.delete_index('quickstart')
    return relevant_response
if __name__ == '__main__':
    app.run(debug=True)