import os
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"
import streamlit as st
from pymongo import MongoClient
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Hugging Face cache (safe path for Streamlit Cloud / Linux)
os.environ['TRANSFORMERS_CACHE'] = '/tmp/hf_cache'

# Connect to MongoDB
try:
    client = MongoClient(os.getenv("MONGO_URI"))
    db = client[os.getenv("MONGO_DBNAME")]
    collection = db[os.getenv("MONGO_COLLECTION")]
except Exception as e:
    st.error("❌ MongoDB connection failed.")
    st.stop()

# Lazy-load model
@st.cache_resource
def load_model():
    st.info("🔄 Loading LLM model...")
    try:
        tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-2")
        model = AutoModelForCausalLM.from_pretrained(
            "microsoft/phi-2",
            torch_dtype=torch.float32,  # CPU-safe
        )
        return tokenizer, model
    except Exception as e:
        st.error("❌ Failed to load model.")
        st.code(str(e))
        return None, None

# Generate MongoDB query from user input
def generate_query(tokenizer, model, user_input, area_of_law):
    prompt = f"""
You are a legal assistant helping to query a MongoDB collection of legal cases.

User input: "{user_input}"
Area of law: "{area_of_law}"

Based on this, generate a MongoDB filter query in JSON format to retrieve relevant documents. Output ONLY the JSON.
"""
    try:
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(**inputs, max_new_tokens=256)
        result = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract JSON
        start = result.find("{")
        end = result.rfind("}") + 1
        query_str = result[start:end]
        query = json.loads(query_str)
        return query
    except Exception as e:
        st.error("❌ Failed to generate or parse the MongoDB query.")
        st.code(result if 'result' in locals() else "No output")
        return None

# --- Streamlit UI ---
st.set_page_config(page_title="Legal Assistant", page_icon="⚖️")
st.title("🧠 Legal Document Assistant")

user_input = st.text_area("📝 Describe the case or legal issue:")
area = st.text_input("⚖️ Area of law (e.g., contract, property, tax):")

if st.button("🔍 Search"):
    if not user_input or not area:
        st.warning("⚠️ Please provide both a case description and an area of law.")
    else:
        with st.spinner("🤔 Thinking..."):
            tokenizer, model = load_model()
            if not tokenizer or not model:
                st.stop()

            query = generate_query(tokenizer, model, user_input, area)

        if query:
            st.subheader("📄 Generated MongoDB Filter Query")
            st.code(json.dumps(query, indent=2))

            try:
                results = list(collection.find(query).limit(5))
                st.subheader(f"📂 Top {len(results)} Matching Results")
                if results:
                    for i, doc in enumerate(results, 1):
                        st.markdown(f"### 🧾 Result {i}")
                        st.json(doc)
                else:
                    st.info("No matching documents found.")
            except Exception as e:
                st.error("❌ Error querying MongoDB.")
                st.code(str(e))
        else:
            st.error("⚠️ Could not execute the query.")
