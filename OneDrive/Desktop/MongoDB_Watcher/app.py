import streamlit as st
from pymongo import MongoClient
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# MongoDB connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGO_DBNAME")]
collection = db[os.getenv("MONGO_COLLECTION")]

# Lazy-load model with Hugging Face token
@st.cache_resource
def load_model():
    st.write("🔄 Loading model...")  # visible progress
    hf_token = os.getenv("HF_TOKEN")

    tokenizer = AutoTokenizer.from_pretrained(
        "mistralai/Mistral-7B-Instruct-v0.1",
        token=hf_token
    )

    model = AutoModelForCausalLM.from_pretrained(
        "mistralai/Mistral-7B-Instruct-v0.1",
        token=hf_token,
        torch_dtype=torch.float16,
        device_map="auto"
    )
    return tokenizer, model

# Generate MongoDB filter query from natural language
def generate_query(tokenizer, model, user_input, area_of_law):
    prompt = f"""
You are a legal assistant helping to query a MongoDB collection of legal cases.

User input: "{user_input}"
Area of law: "{area_of_law}"

Based on this, generate a MongoDB filter query in JSON format to retrieve relevant documents. Output ONLY the JSON.
"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=256)
    result = tokenizer.decode(outputs[0], skip_special_tokens=True)

    try:
        # Extract valid JSON from model output
        start = result.index("{")
        end = result.rindex("}") + 1
        query_str = result[start:end]
        query = json.loads(query_str)
        return query
    except Exception as e:
        st.error("❌ Could not parse query from model output.")
        st.code(result)
        return None

# Streamlit App UI
st.title("🧠 Legal Document Assistant")

user_input = st.text_area("📝 Describe the case or legal issue:")
area = st.text_input("⚖️ Area of law (e.g., contract, property, tax):")

if st.button("🔍 Search"):
    if not user_input or not area:
        st.warning("⚠️ Please provide both a description and area of law.")
    else:
        with st.spinner("Thinking... generating query and fetching results..."):
            tokenizer, model = load_model()
            query = generate_query(tokenizer, model, user_input, area)

        if query:
            st.subheader("📄 Generated MongoDB Filter Query")
            st.code(json.dumps(query, indent=2))

            # Query MongoDB
            results = list(collection.find(query).limit(5))
            st.subheader(f"📂 Top {len(results)} Matching Results")
            if results:
                for i, doc in enumerate(results, 1):
                    st.markdown(f"### 🧾 Result {i}")
                    st.json(doc)
            else:
                st.info("No documents matched the generated query.")
        else:
            st.error("❌ Failed to generate or execute the query.")

