import os
import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
from transformers import pipeline

# Load environment variables
load_dotenv()

# MongoDB config
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_CLUSTER = os.getenv("MONGO_CLUSTER")
MONGO_DBNAME = os.getenv("MONGO_DBNAME")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

# HuggingFace config
HF_TOKEN = os.getenv("HF_TOKEN")

# Set up HuggingFace LLM pipeline
@st.cache_resource
def load_model():
    return pipeline(
        "text-generation",
        model="mistralai/Mistral-7B-Instruct-v0.1",
        token=HF_TOKEN,
        device_map="auto",
        max_new_tokens=512
    )

generator = load_model()

# MongoDB connection
@st.cache_resource
def connect_mongodb():
    try:
        uri = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_CLUSTER}/?retryWrites=true&w=majority"
        client = MongoClient(uri, tls=True, tlsAllowInvalidCertificates=True)
        db = client[MONGO_DBNAME]
        collection = db[MONGO_COLLECTION]
        return collection
    except Exception as e:
        st.error(f"❌ MongoDB connection failed: {e}")
        return None

collection = connect_mongodb()

# Streamlit UI
st.title("⚖️ Legal AI Assistant")
st.write("Ask questions about legal cases in your database.")

user_input = st.text_area("Enter your question here:")

if st.button("Ask"):
    if not user_input:
        st.warning("Please enter a question.")
    elif not collection:
        st.error("Database connection not available.")
    else:
        # Retrieve context from MongoDB
        context_docs = list(collection.find().limit(3))  # You can customize filters
        context_texts = "\n\n".join([doc.get("text", str(doc)) for doc in context_docs])

        # Generate prompt for the LLM
        prompt = f"Context:\n{context_texts}\n\nQuestion: {user_input}\nAnswer:"

        with st.spinner("Analyzing and generating response..."):
            result = generator(prompt)[0]['generated_text']
            answer = result.split("Answer:")[-1].strip()
            st.success("Response:")
            st.write(answer)


