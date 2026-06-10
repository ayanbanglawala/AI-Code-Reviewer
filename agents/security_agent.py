from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
import streamlit as st
load_dotenv()

# Safe path — works from any working directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prompt_path = os.path.join(BASE_DIR, "prompts", "security_prompt.txt")

with open(prompt_path, "r", encoding="utf-8") as f:
    security_prompt = f.read()

llm = ChatMistralAI(
    model="mistral-small-latest",
    api_key=st.secrets.get("MISTRAL_API_KEY"),
    temperature=0.1
)

prompt = PromptTemplate(input_variables=["code"], template=security_prompt)

security_chain = prompt | llm | StrOutputParser()