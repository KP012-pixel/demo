import os
os.environ["STREAMLIT_WATCHER_TYPE"] = "none"

import streamlit as st
from pymongo import MongoClient
import json
from dotenv import load_dotenv

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

# Rule-based MongoDB filter generator (fallback method)
def generate_fallback_query(user_input, area_of_law):
    try:
        keywords = user_input.lower().split()
        filters = [{"$text": {"$search": word}} for word in keywords if len(word) > 3]
        query = {
            "$and": filters + [{"area_of_law": {"$regex": area_of_law, "$options": "i"}}]
        }
        return query
    except Exception as e:
        st.error("❌ Error creating query.")
        st.code(str(e))
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
        with st.spinner("🤔 Analyzing..."):
            query = generate_fallback_query(user_input, area)

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
