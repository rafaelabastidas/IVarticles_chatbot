import streamlit as st
import requests
import os
from io import BytesIO
from PyPDF2 import PdfReader
import google.generativeai as genai

# Step 1: List of document URLs
#urls = [
#    "https://www.imf.org/-/media/Files/Publications/CR/2025/English/1nerea2025001-print-pdf.ashx",
#    "https://www.imf.org/-/media/Files/Publications/CR/2025/English/1zafea2025001-print-pdf.ashx"
#]

urls = [
    "https://github.com/rafaelabastidas/IV-articles/raw/main/1_1zafea2025001-print-pdf.pdf",
    "https://github.com/rafaelabastidas/IV-articles/raw/main/2_1zafea2025001-print-pdf.pdf"
]


# Function to extract text from PDFs
def extract_text_from_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        with BytesIO(response.content) as pdf_file:
            reader = PdfReader(pdf_file)
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text
    else:
        return ""

# Extract text from all documents
all_text = ""
for url in urls:
    all_text += extract_text_from_url(url) + "\n\n"

# Structure the extracted text into sections
sections = {}
lines = all_text.split('\n')

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
You are an assistant. You will answer questions based on the given documents.

{cv_doc}
"""

def query_cv_chatbot(question):
    prompt = f"Here are multiple documents. Answer the following question based on the content:\n\n{cv_prompt}\n\nQuestion: {question}\nAnswer:"
    response = model.generate_content(prompt)  # Request a response from the model
    generated_answer = response.candidates[0].content.parts[0].text.strip()
    return generated_answer

# Step 3: Create the Streamlit app
st.title("IV Articles Chatbot")
st.markdown("""
Welcome. 
This is a chatbot focused on answering questions related to the IMF Article IV Staff Reports documents. 
Let's get started!
""")

# Input box for custom user questions
st.markdown("### Please ask a question:")
custom_question = st.text_input("Ask a question about the articles:")

# Process the user question
if custom_question:
    custom_answer = query_cv_chatbot(custom_question)
    st.markdown(f"**Answer:** {custom_answer}")
