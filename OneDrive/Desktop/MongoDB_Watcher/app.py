import streamlit as st
from transformers import pipeline
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables (optional)
load_dotenv()

# --- MongoDB Connection ---
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DBNAME = os.getenv("MONGO_DBNAME")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION")

try:
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DBNAME]
    collection = db[MONGO_COLLECTION]
    st.success("✅ Connected to MongoDB")
except Exception as e:
    st.error(f"❌ MongoDB connection failed: {e}")

# --- Load Model ---
@st.cache_resource
def load_model():
    try:
        # Using a lightweight model that works without auth token
        model = pipeline("text2text-generation", model="google/flan-t5-small")
        return model
    except Exception as e:
        st.error(f"❌ Failed to load model: {e}")
        return None

generator = load_model()
if generator is None:
    st.stop()

# --- UI ---
st.title("🧠 Legal Case Assistant")

user_input = st.text_area("Enter your legal case description:")
if st.button("Analyze") and user_input:
    with st.spinner("Generating response..."):
        try:
            response = generator(user_input, max_new_tokens=100)[0]["generated_text"]
            st.write("### 📌 Generated Summary")
            st.write(response)
        except Exception as e:
            st.error(f"❌ Generation failed: {e}")

