# legal_chatbot.py

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

print("🔁 Loading model (this may take 1-2 minutes)...")

model_id = "TheBloke/Mistral-7B-Instruct-v0.1-GPTQ"  # Quantized 4-bit version

tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    trust_remote_code=True,
    revision="main"
)

pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)

print("\n✅ Model is ready! Type your legal questions below:")

while True:
    query = input("\n🧑‍⚖️ Ask: ")
    if query.lower() in ["exit", "quit"]:
        break
    response = pipe(query, max_new_tokens=256, do_sample=True, temperature=0.7)
    print("\n🤖 Response:\n", response[0]['generated_text'])
