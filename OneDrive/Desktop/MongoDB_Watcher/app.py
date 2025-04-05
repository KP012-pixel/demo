import streamlit as st
from pymongo import MongoClient
from transformers import pipeline

# --- Load from Streamlit Secrets ---
MONGO_URI = st.secrets["MONGO_URI"]
MONGO_DBNAME = st.secrets["MONGO_DBNAME"]
MONGO_COLLECTION = st.secrets["MONGO_COLLECTION"]

# --- Load HuggingFace Model (no token needed for flan-t5-small) ---
@st.cache_resource
def load_model():
    return pipeline("text2text-generation", model="google/flan-t5-small")

# --- Connect to MongoDB ---
@st.cache_resource
def connect_mongo():
    try:
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DBNAME]
        collection = db[MONGO_COLLECTION]
        st.success("✅ Connected to MongoDB")
        return collection
    except Exception as e:
        st.error(f"❌ Failed to connect to MongoDB: {e}")
        return None

# --- Initialize Model and DB ---
generator = load_model()
collection = connect_mongo()

# --- Streamlit App UI ---
st.title("🧠 Legal Case Assistant")

user_input = st.text_area("Enter your legal case description:")

if st.button("Analyze") and user_input and collection is not None:
    st.markdown("🔍 Searching for related cases...")

    try:
        matching_docs = collection.find({
            "case_text": {"$regex": user_input, "$options": "i"}
        }).limit(3)

        related_texts = [doc["case_text"] for doc in matching_docs]

        if not related_texts:
            st.warning("⚠️ No related cases found. Try a different input.")
            st.stop()

        st.markdown("📄 **Found Related Cases:**")
        for i, text in enumerate(related_texts, 1):
            st.markdown(f"**Case {i}:** {text[:300]}...")

        # Prepare prompt for summarization
        context = " ".join(related_texts)
        prompt = f"Summarize the legal context: {context}. Then, analyze this case: {user_input}"

        st.markdown("🧠 **Generating Response...**")
        result = generator(prompt, max_length=200, do_sample=True)[0]['generated_text']

        st.success("📌 **Generated Summary**")
        st.write(result)

    except Exception as e:
        st.error(f"❌ Something went wrong during analysis: {e}")
