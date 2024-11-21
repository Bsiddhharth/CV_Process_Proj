import logging
from langchain_community.document_loaders import PDFPlumberLoader, TextLoader
import extraction as extr # extraction.py
import streamlit as st
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.DEBUG , format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CVAnalyzer:

    def __init__(self):
        # Initialize Groq LLM
        logger.info("Initializing CVAnalyzer")

        self.llm = extr.initialize_llm()  # Updated to use the new function
        
        logger.info(" LLM initialized")
        # Initialize embeddings (if needed)
        # self.embeddings = HuggingFaceEmbeddings(
        #     model_name="sentence-transformers/all-mpnet-base-v2"
        # )

    def load_document(self, file_path: str) -> str:
        logger.info(f"Loading document from file: {file_path}")

        """Load document based on file type."""

        if file_path.endswith('.pdf'):
            loader = PDFPlumberLoader(file_path)
        else:
            loader = TextLoader(file_path)
        documents = loader.load()

        logger.info(f"Document loaded from {file_path}")

        return " ".join([doc.page_content for doc in documents])

    def extract_cv_info(self, cv_text: str) -> list[extr.cv]: # referring to cv class in extraction.py
        logger.info("Extracting CV information")

        """Extract structured information from CV text using new extraction method."""

        extracted_data = extr.extract_cv_data(cv_text)
        logger.info(f"Extracted {len(extracted_data)} candidate(s) from CV")
        return extracted_data
        # return extr.extract_cv_data(cv_text) 

    def calculate_match_score(self, cv_info: dict, jd_requirements: dict) -> dict:
        logger.info(f"Calculating match score for CV: {cv_info.get('name', 'Unknown')}")

        """Calculate match score between CV and job requirements."""

        score_components = {
            "skills_match": 0,
            "experience_match": 0,
            "overall_score": 0
        }
        
        # Skills matching
        if "skills" in cv_info and "required_skills" in jd_requirements:
            cv_skills = set(skill.lower() for skill in cv_info["skills"])
            required_skills = set(skill.lower() for skill in jd_requirements["required_skills"])
            score_components["skills_match"] = len(cv_skills & required_skills) / len(required_skills)
        
        # Experience matching
        if "years_of_exp" in cv_info and "min_years_experience" in jd_requirements:
            if cv_info["years_of_exp"] >= jd_requirements["min_years_experience"]:
                score_components["experience_match"] = 1.0
            else:
                score_components["experience_match"] = cv_info["years_of_exp"] / jd_requirements["min_years_experience"]
        
        # Calculate overall score (weighted average)
        weights = {"skills_match": 0.5, "experience_match": 0.3}
        score_components["overall_score"] = sum(
            score * weights[component] 
            for component, score in score_components.items() 
            if component != "overall_score"
        )
        
        logger.debug(f"Match score for {cv_info.get('name', 'Unknown')}: {score_components['overall_score']:.2%}")

        return score_components



# def create_cv_shortlisting_page():
#     logger.info("Starting CV shortlisting system")

#     st.title("CV Shortlisting System")
    
#     # Reset analysis state when starting new analysis
#     if 'analysis_started' not in st.session_state:
#         st.session_state.analysis_started = False
    
#     # Job Description Input
#     st.header("Job Description")
#     jd_text = st.text_area("Enter the job description",
#                            value=st.session_state.jd_text if 'jd_text' in st.session_state else "")
    
#     if jd_text:
#         st.session_state.jd_text = jd_text
    
#     # Job Requirements Input
#     st.header("Job Requirements")
#     min_years = st.number_input("Minimum years of experience", 
#                                min_value=0, 
#                                value=st.session_state.min_years if 'min_years' in st.session_state else 3)
    
#     required_skills = st.text_input("Required skills (comma-separated)", 
#                                    value=','.join(st.session_state.required_skills_list) if 'required_skills_list' in st.session_state else "")
    
#     required_skills_list = [skill.strip() for skill in required_skills.split(",") if skill.strip()]
    
#     # Update session state
#     st.session_state.required_skills_list = required_skills_list
#     st.session_state.min_years = min_years

#     # CV Upload
#     st.header("Upload CVs")
#     uploaded_files = st.file_uploader("Choose CV files", 
#                                     accept_multiple_files=True, 
#                                     type=['pdf', 'txt'], 
#                                     key="cv_upload")
    
#     if uploaded_files:
#         st.session_state.uploaded_files = uploaded_files
#         st.session_state.analysis_started = True

#     # Analysis Button
#     if st.button("Analyze CVs") and uploaded_files and jd_text:
#         st.session_state.results = []  # Reset results
#         st.session_state.processed_cvs = {}  # Reset processed CVs
        
        # with st.spinner('Analyzing CVs...'):
        #     try:
        #         analyzer = CVAnalyzer()
                
        #         # Prepare job requirements
        #         job_requirements = {
        #             "min_years_experience": st.session_state.min_years,
        #             "required_skills": st.session_state.required_skills_list
        #         }
                
        #         # Process each CV
        #         for uploaded_file in uploaded_files:
        #             cv_text = extr.process_file(uploaded_file)
                    
        #             try:
        #                 # Extract CV information
        #                 candidates = analyzer.extract_cv_info(cv_text)
                        
        #                 for idx, candidate in enumerate(candidates):
        #                     # Calculate match scores
        #                     match_scores = analyzer.calculate_match_score(
        #                         candidate.__dict__, 
        #                         job_requirements
        #                     )
                            
        #                     # Store results
        #                     result = {
        #                         "Name": candidate.name or "Unknown",
        #                         "Experience (Years)": candidate.years_of_exp or 0,
        #                         "Skills": ", ".join(candidate.skills) if candidate.skills else "None",
        #                         "Certifications": ", ".join(candidate.certifications) if candidate.certifications else "None",
        #                         "Skills Match": f"{match_scores['skills_match']:.2%}",
        #                         "Experience Match": f"{match_scores['experience_match']:.2%}",
        #                         "Overall Score": f"{match_scores['overall_score']:.2%}"
        #                     }
                            
        #                     st.session_state.results.append(result)
                            
        #                     # Store processed CV data for interview questions
        #                     st.session_state.processed_cvs[f"{candidate.name}_{idx}"] = {
        #                         "cv_text": cv_text,
        #                         "candidate": candidate,
        #                         "match_scores": match_scores
        #                     }
                            
        #             except Exception as e:
        #                 logger.error(f"Error processing CV: {str(e)}")
        #                 st.error(f"Error processing CV: {str(e)}")
                
        #         # Mark analysis as complete
        #         st.session_state.analysis_complete = True
                
        #         # Display results
        #         if st.session_state.results:
        #             df = pd.DataFrame(st.session_state.results)
        #             df = df.sort_values("Overall Score", ascending=False)
        #             st.dataframe(df)
                    
        #             # Save top candidates
        #             st.session_state.top_candidates = df.head()
        #         else:
        #             logger.warning("No valid candidates found")
        #             st.warning("No valid candidates found in the uploaded CVs")
                    
        #     except Exception as e:
        #         logger.error(f"Analysis error: {str(e)}")
        #         st.error(f"An error occurred during analysis: {str(e)}")
        #         st.session_state.analysis_complete = False
    
#     # Display analysis status
#     if st.session_state.get('analysis_complete', False):
#         st.success("CV analysis complete! You can now proceed to generate interview questions.")


def create_cv_shortlisting_page():
    logger.info("Starting CV shortlisting system")

    # Initialize session state if not already initialized
    if 'jd_text' not in st.session_state:
        st.session_state.jd_text = ""
    if 'min_years' not in st.session_state:
        st.session_state.min_years = 3
    if 'required_skills_list' not in st.session_state:
        st.session_state.required_skills_list = []
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = None
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False

    st.title("CV Shortlisting System")
    
    # Job Description Input
    st.header("Job Description")
    jd_text = st.text_area("Enter the job description", value=st.session_state.jd_text)
    if jd_text:
        st.session_state.jd_text = jd_text
    
    # Job Requirements Input
    st.header("Job Requirements")
    min_years = st.number_input("Minimum years of experience", 
                               min_value=0, 
                               value=st.session_state.min_years,
                               )
    
    required_skills = st.text_input("Required skills (comma-separated)", 
                                   value=','.join(st.session_state.required_skills_list) if st.session_state.required_skills_list else "")
    
    required_skills_list = [skill.strip() for skill in required_skills.split(",") if skill.strip()]
    
    if required_skills_list:
        st.session_state.required_skills_list = required_skills_list
    if min_years:
        st.session_state.min_years = min_years

    # CV Upload
    st.header("Upload CVs")
    uploaded_files = st.file_uploader("Choose CV files", 
                                    accept_multiple_files=True, 
                                    type=['pdf', 'txt'], 
                                    key="unique_cv_upload")
    
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files

    if st.button("Analyze CVs") and uploaded_files and jd_text:
        logger.info("Analyzing uploaded CVs")
        with st.spinner('Analyzing CVs...'):
            analyzer = CVAnalyzer()
            
            # Prepare job requirements
            job_requirements = {
                "min_years_experience": st.session_state.min_years,
                "required_skills": st.session_state.required_skills_list
            }
            
            results = []
            st.session_state.results = []  # Reset results for new analysis

            # Process each CV
            for uploaded_file in uploaded_files:
                cv_text = extr.process_file(uploaded_file)
                
                try:
                    candidates = analyzer.extract_cv_info(cv_text)
                    
                    for candidate in candidates:
                        match_scores = analyzer.calculate_match_score(
                            candidate.__dict__, 
                            job_requirements
                        )
                        
                        result = {
                            "Name": candidate.name or "Unknown",
                            "Experience (Years)": candidate.years_of_exp or 0,
                            "Skills": ", ".join(candidate.skills) if candidate.skills else "None",
                            "Certifications": ", ".join(candidate.certifications) if candidate.certifications else "None",
                            "Skills Match": f"{match_scores['skills_match']:.2%}",
                            "Experience Match": f"{match_scores['experience_match']:.2%}",
                            "Overall Score": f"{match_scores['overall_score']:.2%}"
                        }
                        
                        results.append(result)
                        st.session_state.results.append(result)
                        
                except Exception as e:
                    logger.error(f"Error processing CV: {str(e)}")
            
        # Display results
        logger.info(f"Displaying analyzed results for {len(results)} candidate(s)")
        
        if st.session_state.results:
            df = pd.DataFrame(st.session_state.results)
            df = df.sort_values("Overall Score", ascending=False)
            st.dataframe(df)
            st.session_state.analysis_complete = True
        else:
            logger.warning("No valid candidates found in uploaded CVs")
            st.error("No valid results found from CV analysis")
            st.session_state.analysis_complete = False