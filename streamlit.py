
#cd "C:/Users/RAFAELAB/OneDrive - Inter-American Development Bank Group/Documents/PBLs/Depth/Code"
#streamlit run .\streamlit.py
import streamlit as st
import requests
import os
from io import BytesIO
from PyPDF2 import PdfReader
import google.generativeai as genai

# Step 1: Download and extract the CV text
url = "https://www.imf.org/-/media/Files/Publications/CR/2025/English/1nerea2025001-print-pdf.ashx"
response = requests.get(url)

with BytesIO(response.content) as pdf_file:
    reader = PdfReader(pdf_file)
    cv_text = ""
    for page in reader.pages:
        cv_text += page.extract_text()

# Structure the CV text into sections
sections = {}
lines = cv_text.split('\n')

current_section = None
for line in lines:
    if line.isupper():  # Assuming section headers are in uppercase
        current_section = line
        sections[current_section] = []
    elif current_section:
        sections[current_section].append(line)

# Convert sections to a readable format
for section, content in sections.items():
    sections[section] = " ".join(content)

cv_doc = "\n".join(
    f"{section}:\n{content}" for section, content in sections.items()
)

# Step 2: Configure the generative AI model
api_key = os.getenv('API_KEY')
if api_key is None:
    raise ValueError("API_KEY not found. Please set the environment variable.")
genai.configure(api_key=api_key)

generation_config = {
    "temperature": 0,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 1000,
}

model = genai.GenerativeModel(model_name='gemini-1.5-flash', generation_config=generation_config)

cv_prompt = f"""
You are a assistant. You will answer questions based on the given article.

{cv_doc}
"""

def query_cv_chatbot(question):
    prompt = f"Here is an article. Answer the following question based on the article:\n\n{cv_prompt}\n\nQuestion: {question}\nAnswer:"
    response = model.generate_content(prompt)  # Request a response from the model
    generated_answer = response.candidates[0].content.parts[0].text.strip()
    return generated_answer

# Step 3: Create the Streamlit app
st.title("IV Articles Chatbot")
st.markdown("""
#Let's get started
""")



# Input box for custom user questions
st.markdown("### Please ask a question:")
custom_question = st.text_input("Ask a question about the article:")

# Process the user question
if custom_question:
    custom_answer = query_cv_chatbot(custom_question)
    st.markdown(f"**Answer:** {custom_answer}")



