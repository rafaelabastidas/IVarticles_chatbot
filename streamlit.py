import os
import requests
from io import BytesIO
from PyPDF2 import PdfReader
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin

# Set up Selenium WebDriver with proper initialization
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Base URL for the page to scrape
base_url = "https://www.imf.org/en/Publications/WP/Issues/2022/12/20/IMF-Working-Paper-Series"  # Example URL

# Function to scrape PDFs from a specific page
def scrape_pdfs(page_url):
    driver.get(page_url)

    # Wait for the page to load fully
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//a[@class="CoveoResultLink"]')))

    # Find all the links with the specific class 'CoveoResultLink'
    links = driver.find_elements(By.XPATH, '//a[@class="CoveoResultLink"]')

    # Extract the PDF links
    pdf_links = []
    for link in links:
        href = link.get_attribute('href')
        if href and '.ashx' in href:
            pdf_links.append(href)

    return pdf_links

# Download and extract the CV text from the PDF link
def extract_pdf_text(pdf_url):
    response = requests.get(pdf_url)
    with BytesIO(response.content) as pdf_file:
        reader = PdfReader(pdf_file)
        cv_text = ""
        for page in reader.pages:
            cv_text += page.extract_text()
    return cv_text

# Structure the CV text into sections
def structure_cv_text(cv_text):
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
    return cv_doc

# Configure the generative AI model
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

# Function to query the chatbot
def query_cv_chatbot(question, cv_doc):
    prompt = f"Here is an article. Answer the following question based on the article:\n\n{cv_doc}\n\nQuestion: {question}\nAnswer:"
    response = model.generate_content(prompt)  # Request a response from the model
    generated_answer = response.candidates[0].content.parts[0].text.strip()
    return generated_answer

# Streamlit App
st.title("IV Articles Chatbot")
st.markdown("""
Welcome. 
This is a chatbot focused on answering questions related to the IMF Article IV Staff Reports documents. 
Let's get started
""")

# Input box for custom user questions
st.markdown("### Please ask a question:")
custom_question = st.text_input("Ask a question about the article:")

# Scrape PDFs from multiple pages
all_pdf_links = []

# Define the number of pages you want to scrape (can adjust this value)
pages_to_scrape = 5  # Example: scraping 5 pages

for page_num in range(pages_to_scrape):
    # Adjust the URL to the correct page number
    if page_num == 0:
        page_url = base_url + "#sort=%40imfdate%20descending"
    else:
        page_url = base_url + f"#first={page_num * 10}&sort=%40imfdate%20descending"

    st.write(f"Scraping page {page_num + 1}...")  # Show scraping status in Streamlit

    # Get the PDF links for this page
    pdf_links = scrape_pdfs(page_url)
    all_pdf_links.extend(pdf_links)

# Check if there are any PDFs to process
if all_pdf_links:
    # Extract text from the first PDF
    pdf_text = extract_pdf_text(all_pdf_links[0])  # Process the first PDF link
    cv_doc = structure_cv_text(pdf_text)

    # Process the user question
    if custom_question:
        custom_answer = query_cv_chatbot(custom_question, cv_doc)
        st.markdown(f"**Answer:** {custom_answer}")
else:
    st.markdown("No PDFs found on the pages.")
