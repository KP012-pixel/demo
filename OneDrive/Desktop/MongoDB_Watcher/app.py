import streamlit as st
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from transformers import pipeline
import hashlib

# Load Streamlit secrets
MONGO_URI = st.secrets["MONGO_URI"]
MONGO_DBNAME = st.secrets["MONGO_DBNAME"]
MONGO_COLLECTION = st.secrets["MONGO_COLLECTION"]
HF_TOKEN = st.secrets["HF_TOKEN"]

@st.cache_resource
def load_model():
    return pipeline("text2text-generation", model="google/flan-t5-small", token=HF_TOKEN)

@st.cache_resource
def connect_mongo():
    try:
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DBNAME]
        collection = db[MONGO_COLLECTION]
        return collection
    except Exception as e:
        st.error(f"❌ Failed to connect to MongoDB: {e}")
        return None

# Load model and MongoDB
generator = load_model()
collection = connect_mongo()

# --- Streamlit UI ---
st.title("🧠 Legal Case Assistant")

user_input = st.text_area("Enter your legal case description:")

if st.button("Analyze") and user_input and collection is not None:
    st.markdown("🔍 Searching for related cases...")

    # Find similar documents in MongoDB
    matching_docs = collection.find({
        "case_text": {"$regex": user_input, "$options": "i"}
    }).limit(3)

    related_texts = [doc["case_text"] for doc in matching_docs]

    if related_texts:
        st.markdown("📄 **Found Related Cases:**")
        for i, text in enumerate(related_texts, 1):
            st.markdown(f"**Case {i}:** {text[:300]}...")

        # Join context with user input
        context = " ".join(related_texts)
        prompt = f"Summarize the legal context: {context}. Then, analyze this case: {user_input}"

        st.markdown("🧠 **Generating Response...**")
        result = generator(prompt, max_length=200, do_sample=True)[0]['generated_text']
        
        st.success("📌 **Generated Summary**")
        st.write(result)

    else:
        st.warning("⚠️ No related cases found. Try a different input.")
