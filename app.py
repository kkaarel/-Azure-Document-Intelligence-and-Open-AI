import os
import streamlit as st
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient, AnalysisFeature
from azure.core.exceptions import HttpResponseError
from openai import AzureOpenAI
import json
import pandas as pd


##Parts of the code are form azure samples
#https://github.com/Azure-Samples/document-intelligence-code-samples/blob/v3.1(2023-07-31-GA)/Python(v3.1)/Read_model/sample_analyze_read.py

st.set_page_config(
    page_title="Analyse documents",
    page_icon="🧊",
    layout="wide"
)

AZURE_OPENAI_API_KEY =  st.secrets["AZURE_OPENAI_API_KEY"] 
AZURE_OPENAI_ENDPOINT = st.secrets["AZURE_OPENAI_ENDPOINT"]

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,  
    api_version="2024-08-01-preview",
    azure_endpoint = AZURE_OPENAI_ENDPOINT
    )

deployment_name=st.secrets["deploymentname"]

def get_response(prompt):
    if not prompt:
        st.error("Prompt is empty or None.")
        return None

    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You will receive data from an invoice. Structure it, add into columns based on the data"},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=4096
        )
        response_dict = response.model_dump()  

        content = response_dict["choices"][0]["message"]["content"].strip() 
        

        return content 
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None


def analyze_read(file):

    endpoint = st.secrets["DOCUMENTATIONAPI"] 
    key = st.secrets["DOCUMENTATIONAPI_KEY"]

    document_analysis_client = DocumentAnalysisClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )


    poller = document_analysis_client.begin_analyze_document(
        "prebuilt-read", document=file, features=[AnalysisFeature.LANGUAGES]
    )
    result = poller.result()

    paragraphs_content = []
    if len(result.paragraphs) > 0:
        for paragraph in result.paragraphs:
            paragraphs_content.append(paragraph.content)

    st.write("----------------------------------------")
    

    return " ".join(paragraphs_content)

def split_prompt(prompt, max_length):

    return [prompt[i:i + max_length] for i in range(0, len(prompt), max_length)]

def main():
    st.title("Document Analysis with Azure Document Intelligence and Open AI")

    
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "jpg", "png"])
    
    if uploaded_file is not None:
        try:
            prompt = analyze_read(uploaded_file)
            result = get_response(prompt)
            st.header("Analysed by Azure Document Intelligence")
            st.caption("Data form the invoice")
            st.write(prompt)
            st.header("Analysed by Azure Open AI")
            st.caption("Module used gpt-4o")
            st.write(result)

        except HttpResponseError as error:
            st.error(
                "For more information about troubleshooting errors, see the following guide: "
                "https://aka.ms/azsdk/python/formrecognizer/troubleshooting"
            )
            if error.error is not None:
                if error.error.code == "InvalidFile":
                    st.error(f"Received an invalid File error: {error.error}")
                if error.error.code == "InvalidRequest":
                    st.error(f"Received an invalid request error: {error.error}")
                raise
            if "Invalid request".casefold() in error.message.casefold():
                st.error(f"Uh-oh! Seems there was an invalid request: {error}")
            raise

if __name__ == "__main__":
    main()