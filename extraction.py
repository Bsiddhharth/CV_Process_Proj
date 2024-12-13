import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
import os
import tempfile
import streamlit as st
from langchain_community.document_loaders import PDFPlumberLoader, TextLoader


# logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Defining the CV structure using Pydantic for structured output
class cv(BaseModel):
    name: Optional[str] = Field(default=None, description="Name of candidate")
    skills: Optional[list[str]] = Field(default=None, description="Skills of candidate")
    certifications: Optional[list[str]] = Field(default=None, description="Certificates of candidate")
    years_of_exp: Optional[int] = Field(default=None, description="Years of experience")

# Defining the data structure that contains a list of CVs
class data(BaseModel):
    candidates: list[cv]

def create_prompt_template() -> ChatPromptTemplate:

    logger.info("Creating the prompt template for CV extraction")

    """Create the prompt template for CV extraction."""
    
    return ChatPromptTemplate.from_messages(
        [
            ("system",
        "You are an expert extraction algorithm. Your job is to extract the following specific information from the given text:"
         "- Name of the candidate"
         "- Skills"
         "- Certifications (Look for terms such as 'Certified,' 'Certification,' 'Certificate')"
         "- years_of_exp (Extract only the number of years. If an approximation is given (e.g., '5+ years'), return the lower bound (e.g., '5').)"
         "If you cannot find the value for a specific attribute, return null for that attribute's value."
         "The 'years of experience' can be mentioned in various formats (e.g., '5+ years', '5 years', 'since 2010'). "
         "Extract it accurately, even if it's mentioned in different contexts like a professional summary or work experience. "
         "If multiple jobs are listed, you can calculate the experience from the work history."
        "Certifications are usually found under headers like 'Certifications,' 'Professional Certificates,' or similar. They might include phrases like 'AWS Certified Developer,' 'MongoDB Developer Associate,' etc."
        ),
            ("human", "{text}")
        ]
    )

def initialize_llm() -> ChatGroq:
    logger.info("Initializing LLM")

    """Initialize the language model."""

    # os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key is None:
        try:
            groq_api_key = st.secrets["GROQ_API_KEY"]
        except Exception as e:
            st.error("GROQ_API_KEY is not set in the environment variables or Streamlit secrets.")
            groq_api_key = None
    # groq_api_key = st.secrets["GROQ_API_KEY"]

    

    if not groq_api_key:
        logger.error("GROQ_API_KEY is not set")
        raise ValueError("GROQ_API_KEY environment variable is missing.")


    return ChatGroq(groq_api_key=groq_api_key, model_name="llama-3.3-70b-versatile", temperature=0.6)


def extract_cv_data(text: str) -> list[cv]:
    logger.info("Extracting CV data from text")

    """Extract data from the text using the language model."""

    prompt = create_prompt_template()
    llm = initialize_llm()

    # creating a chain to extract structred ouput from the text using schema
    runnable = prompt | llm.with_structured_output(schema=data)
    response = runnable.invoke({"text": text})

    logger.info(f"Extracted {len(response.candidates)} candidate(s) from the text")
    
    return response.candidates  # returns the list of candidates

def process_file(uploaded_files) -> str:
    logger.info(f"Processing file: {uploaded_files.name}")

    """Process the uploaded file and return the text."""

    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_files.name)[1]) as tmp_file:
        tmp_file.write(uploaded_files.getvalue())
        tmp_path = tmp_file.name
    try:
        if tmp_path.endswith('.pdf'):
            loader = PDFPlumberLoader(tmp_path)
            logger.info(f"Loaded PDF file: {tmp_path}")

        else:
            loader = TextLoader(tmp_path)
            logger.info(f"Loaded text file: {tmp_path}")

        documents = loader.load()
        # return " ".join([doc.page_content for doc in documents])
        text_content = " ".join([doc.page_content for doc in documents])
        logger.info(f"Extracted text from file: {uploaded_files.name}")
        return text_content
    
    finally:
        logger.info(f"Deleting temporary file: {tmp_path}")
        os.unlink(tmp_path)

def display_candidates_info(candidates_list: list[cv]):
    logger.info(f"Displaying information for {len(candidates_list)} candidate(s)")

    """Display the extracted candidates' information in a table."""
    
    logger.debug(f"Candidate list: {candidates_list}")

    data = []
    for candidate in candidates_list:
        data.append({
            "Name": candidate.name,
            "Skills": ", ".join(candidate.skills) if candidate.skills else 'None',
            "Certifications": ", ".join(candidate.certifications) if candidate.certifications else 'None',
            "Years of Experience": candidate.years_of_exp if candidate.years_of_exp else 'None'
        })

    st.write("### Candidates Information")
    st.table(data)
    logger.debug("Displayed candidates' information in table")
    # print(candidates_list)

# Try this to see the working of extraction
# Streamlit file uploader and extraction logic
# uploaded_files = st.file_uploader(" Upload the CV: ", type=['pdf', 'txt'],key="unique_cv_upload")
# if uploaded_files is not None:
#     text = process_file(uploaded_files)
#     # text = ep.text
#     candidates_list = extract_cv_data(text)
#     display_candidates_info(candidates_list)
