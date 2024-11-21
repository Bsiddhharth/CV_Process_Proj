import streamlit as st
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
import os
import tempfile
import json
from extraction import extract_cv_data, process_file, display_candidates_info  # importing from your extraction.py

# Initialize environment variables
os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

class InterviewQuestionGenerator:
    def __init__(self):
        self.llm = ChatGroq(
            groq_api_key=groq_api_key,
            # model_name="mixtral-8x7b-32768",
            model_name = "llama3-8b-8192",
            temperature=0.7,
            max_tokens=4096
        )
        
        # The prompt template to generate questions based on extracted CV data
        self.question_template = """
        Based on the following CV excerpt, generate 5 specific basic technical interview questions 
        that are directly related to the candidate's experience and skills. Make sure the 
        questions test both their claimed knowledge and problem-solving abilities.

        CV Excerpt:
        {cv_text}

        Skills Mentioned:
        {skills}

       Return the questions in the following text format:

        (bold)
        Question 1:\n

        - Technical_question: "Your question here" \n

        - Follow_up_question: "Deep dive question here" \n

        - What_to_listen_for: "Key points to listen for here" \n

        \n\n
        Question 2:

        - Technical_question: "Your question here" \n
 
        - Follow_up_question: "Deep dive question here" \n

        - What_to_listen_for: "Key points to listen for here" \n


        
        Make sure to follow this format exactly, with the correct structure and labels for each question.
        

        (Repeat for all 5 questions)
        
        Be sure to make each question clear and actionable, and align it with the skills mentioned in the CV.
        """
        
        # Using ChatPromptTemplate for question generation
        self.question_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.question_template),
                ("human", "{cv_text}\n{skills}")
            ]
        )
        
    def generate_questions(self, cv_text: str, skills: str) -> str:
        """Generate interview questions based on CV text and skills."""
        runnable = self.question_prompt | self.llm  # Using Runnable instead of LLMChain
        questions = runnable.invoke({
            "cv_text": cv_text,
            "skills": skills
        })
        return questions


def create_interview_questions_page():
    # Initializing session state variables since they dont exist at first
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'cv_text' not in st.session_state:
        st.session_state.cv_text = None
    if 'candidates_list' not in st.session_state:
        st.session_state.candidates_list = None
    if 'generated_questions' not in st.session_state:
        st.session_state.generated_questions = None

    st.title("Interview Question Generator")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload a CV", type=['pdf', 'txt'])
    
    # Update session state when new file is uploaded
    if uploaded_file is not None and (st.session_state.uploaded_file is None or 
                                    uploaded_file.name != st.session_state.uploaded_file.name):
        st.session_state.uploaded_file = uploaded_file
        st.session_state.cv_text = None  # Reset CV text
        st.session_state.candidates_list = None  # Reset candidates
        st.session_state.generated_questions = None  # Reset questions
    
    # Process file if it exists in session state
    if st.session_state.uploaded_file is not None:
        # Only process the file if we haven't already
        if st.session_state.cv_text is None:
            st.session_state.cv_text = process_file(st.session_state.uploaded_file)
            st.session_state.candidates_list = extract_cv_data(st.session_state.cv_text)

        # Display candidates info if available
        if st.session_state.candidates_list:
            display_candidates_info(st.session_state.candidates_list)
            
            # Generate questions if not already generated
            if st.session_state.generated_questions is None:
                candidate = st.session_state.candidates_list[0]
                generator = InterviewQuestionGenerator()
                questions = generator.generate_questions(
                    cv_text=st.session_state.cv_text,
                    skills=", ".join(candidate.skills)
                )
                st.session_state.generated_questions = questions.content

            # Display the generated questions
            st.subheader("Recommended Interview Questions")
            st.markdown(st.session_state.generated_questions)