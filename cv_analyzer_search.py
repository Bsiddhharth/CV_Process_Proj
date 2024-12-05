import streamlit as st
import pandas as pd
from langchain_groq import ChatGroq
from groq import Groq
from jobspy import scrape_jobs
from resume_advance_analysis import *
from extraction import *
# (
#     cv,  
#     extract_cv_data, 
#     process_file,  # File processing function
#     initialize_llm,  # LLM initialization function
#     display_candidates_info  # Candidate info display function
# )
from typing import List, Dict, Any
import json
import re
import os
import logging


def make_clickable_link(link):
    return f'<a href="{link}" target="_blank">{link}</a>'



# os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
# groq_api_key = os.getenv("GROQ_API_KEY")
groq_api_key = st.secrets["GROQ_API_KEY"]

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JobSuggestionEngine:
    def __init__(self):

        # self.llm = ChatGroq(
        #     groq_api_key = groq_api_key,
        #     model_name="llama-3.1-70b-versatile",
        #     temperature=0.7,
        #     max_tokens=4096
        # )
        self.client = Groq(api_key=groq_api_key)
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
                Extracting JSON from LLM
        """
        try:
            logger.debug("Extracting JSON from LLM response")
            # Clean and extract JSON
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return {}
        
        except Exception as e:
            st.error(f"JSON Extraction Error: {e}")
            logger.error(f"JSON Extraction Error: {e}")
            return {}
    
    def generate_job_suggestions(self, resume_data: cv) -> List[Dict[str, str]]:

        logger.info("Generating job suggestions based on resume")

        prompt = f"""Based on the following resume details, provide job suggestions:

            Resume Details:
            - Skills: {', '.join(resume_data.skills or [])}
            - Certifications: {', '.join(resume_data.certifications or [])}
            - Years of Experience: {resume_data.years_of_exp or 0}
            
            Tasks:
            1. Suggest most potential 3 job roles that match the profile
            2. Include job role, brief description, and why it's suitable
            3. Respond in strict JSON format

            Required JSON Structure:
            {{
                "job_suggestions": [
                    {{
                        "role": "Job Role",
                        "description": "Brief job description",
                        "suitability_reason": "Why this role matches the resume"
                    }}
                ]
            }}


            """
        try:

            logger.debug(f"Calling Groq API with prompt: {prompt[:100]}...") # start of api call
            
            # API call to the Groq client for chat completions
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a career advisor generating job suggestions based on resume details."},
                    {"role": "user", "content": prompt}
                ],
                model="llama3-8b-8192",  
                temperature=0.7,  
                max_tokens=1024, 
                top_p=1,
                stop=None,
                stream=False
            )
            
            # Extract and parse the JSON response from the completion
            response_text = chat_completion.choices[0].message.content
            suggestions_data = self._extract_json(response_text)

            logger.info(f"Job suggestions generated: {len(suggestions_data.get('job_suggestions', []))} found")
            
            # Return job suggestions, if not found -> empty list 
            return suggestions_data.get('job_suggestions', [])
        
        except Exception as e:
            st.error(f"Job Suggestion Error: {e}")
            logger.error(f"Job Suggestion Error: {e}")
            return []

def Job_assistant():
    st.title("📄 Job Suggestion & Search Assistant")

    # Initialize session state for resume analysis tab
    if 'uploaded_resume' not in st.session_state:
        st.session_state.uploaded_resume = None
    if 'resume_data' not in st.session_state:
        st.session_state.resume_data = None
    if 'job_suggestions' not in st.session_state:
        st.session_state.job_suggestions = []
    if 'improvement_suggestions' not in st.session_state:
        st.session_state.improvement_suggestions = {}
    
    # Initialize session state for job search tab
    if 'site_name' not in st.session_state:
        st.session_state.site_name = ["indeed", "glassdoor"]
    if 'search_term' not in st.session_state:
        st.session_state.search_term = "software engineer"
    if 'location' not in st.session_state:
        st.session_state.location = "San Francisco, CA"
    if 'results_wanted' not in st.session_state:
        st.session_state.results_wanted = 20
    if 'hours_old' not in st.session_state:
        st.session_state.hours_old = 72
    if 'country_indeed' not in st.session_state:
        st.session_state.country_indeed = "USA"
    if 'job_search_results' not in st.session_state:
        st.session_state.job_search_results = pd.DataFrame()
    
    # Tabs for functionalities
    tab1, tab2 = st.tabs(["Resume Analysis", "Direct Job Search"])
    
    
    with tab1:
        st.header("Resume Analysis & Job Suggestions")
        
        # File Upload
        uploaded_resume = st.file_uploader(
            "Upload Resume", 
            type=['pdf', 'txt'],
            help="Upload your resume in PDF or TXT format"
        )
        
        # # Initialize LLM 
        # try:
        #     llm = initialize_llm()
        #     logger.info("LLM initialized successfully")

        # except Exception as e:
        #     st.error(f"LLM Initialization Error: {e}")
        #     logger.error(f"LLM Initialization Error: {e}")
        #     st.stop()
        
        if uploaded_resume:
            st.session_state.uploaded_resume = uploaded_resume
            # Process Resume
            with st.spinner("Analyzing Resume..."):
                try:
                    # Extract resume text
                    resume_text = process_file(uploaded_resume)
                    logger.info("Resume extracted successfully")
                    
                    # Extract structured CV data
                    candidates = extract_cv_data(resume_text)
                    
                    if not candidates:
                        st.error("Could not extract resume data")
                        logger.error("No candidates extracted from resume")
                        st.stop()
                    
                    st.session_state.resume_data = candidates[0]

                    # Display extracted candidate information
                    st.subheader("Resume Analysis")
                    display_candidates_info(candidates)
                    
                    resume_data = candidates[0]
                
                except Exception as e:
                    st.error(f"Resume Processing Error: {e}")
                    logger.error(f"Resume Processing Error: {e}")
                    st.stop()
            
            # Initialize Job Suggestion Engine
            if st.session_state.resume_data:
                suggestion_engine = JobSuggestionEngine()
                logger.info("Job_Suggestion_Engine initialized")
                
                # Generate Job Suggestions
                job_suggestions = suggestion_engine.generate_job_suggestions(resume_data)
                logger.info(f"Generated {len(job_suggestions)} job suggestions")

                st.session_state.job_suggestions = job_suggestions

                # Display Job Suggestions
                st.header("🎯 Job Suggestions")
                # for suggestion in job_suggestions:
                for suggestion in st.session_state.job_suggestions:
                    with st.expander(f"{suggestion.get('role', 'Unnamed Role')}"):
                        st.write(f"**Description:** {suggestion.get('description', 'No description')}")
                        st.write(f"**Suitability:** {suggestion.get('suitability_reason', 'Not specified')}")


            try:
                    # Extract resume text
                    resume_text = process_file(uploaded_resume)
                    logger.info("Resume text extracted again for improvement suggestions")

                    # Initialize Resume Improvement Engine
                    improvement_engine = ResumeImprovementEngine()
                    
                    # Generate Improvement Suggestions
                    improvement_suggestions = improvement_engine.generate_resume_improvement_suggestions(resume_text)
                    logger.info("Resume improvement suggestions generated")
                    st.session_state.improvement_suggestions = improvement_suggestions

                    # Display Suggestions
                    st.subheader("🔍 Comprehensive Resume Analysis")
                    
                    # Overall Assessment
                    if improvement_suggestions.get('overall_assessment'):
                        with st.expander("📊 Overall Assessment"):
                            st.write("**Strengths:**")
                            for strength in improvement_suggestions['overall_assessment'].get('strengths', []):
                                st.markdown(f"- {strength}")
                            
                            st.write("**Weaknesses:**")
                            for weakness in improvement_suggestions['overall_assessment'].get('weaknesses', []):
                                st.markdown(f"- {weakness}")
                    
                    # Section Recommendations
                    if improvement_suggestions.get('section_recommendations'):
                        with st.expander("📝 Section-by-Section Recommendations"):
                            for section, details in improvement_suggestions['section_recommendations'].items():
                                st.subheader(f"{section.replace('_', ' ').title()} Section")
                                st.write(f"**Current Status:** {details.get('current_status', 'No assessment')}")
                                
                                st.write("**Improvement Suggestions:**")
                                for suggestion in details.get('improvement_suggestions', []):
                                    st.markdown(f"- {suggestion}")
                    
                    # Additional Insights
                    st.subheader("✨ Additional Recommendations")
                    
                    # Writing Improvements
                    if improvement_suggestions.get('writing_improvements'):
                        with st.expander("✍️ Writing & Formatting Advice"):
                            st.write("**Language Suggestions:**")
                            for lang_suggestion in improvement_suggestions['writing_improvements'].get('language_suggestions', []):
                                st.markdown(f"- {lang_suggestion}")
                            
                            st.write("**Formatting Advice:**")
                            for format_advice in improvement_suggestions['writing_improvements'].get('formatting_advice', []):
                                st.markdown(f"- {format_advice}")
                    
                    # Additional Sections
                    if improvement_suggestions.get('additional_sections_recommended'):
                        with st.expander("📋 Suggested Additional Sections"):
                            for section in improvement_suggestions['additional_sections_recommended']:
                                st.markdown(f"- {section}")
                    
                    # Keyword Optimization
                    if improvement_suggestions.get('keyword_optimization'):
                        with st.expander("🔑 Keyword & ATS Optimization"):
                            st.write("**Missing Industry Keywords:**")
                            for keyword in improvement_suggestions['keyword_optimization'].get('missing_industry_keywords', []):
                                st.markdown(f"- {keyword}")
                            
                            st.write(f"**ATS Compatibility Score:** {improvement_suggestions['keyword_optimization'].get('ats_compatibility_score', 'Not available')}")
                    
                    # Career Positioning
                    if improvement_suggestions.get('career_positioning'):
                        with st.expander("🎯 Career Positioning"):
                            st.write("**Personal Branding Suggestions:**")
                            for branding_suggestion in improvement_suggestions['career_positioning'].get('personal_branding_suggestions', []):
                                st.markdown(f"- {branding_suggestion}")
                            
                            st.write("**Skill Highlighting Recommendations:**")
                            for skill_suggestion in improvement_suggestions['career_positioning'].get('skill_highlighting_recommendations', []):
                                st.markdown(f"- {skill_suggestion}")
                
            except Exception as e:
                    st.error(f"Resume Improvement Analysis Error: {e}")
                    logger.error(f"Resume Improvement Analysis Error: {e}")


    with tab2:
        st.header("🔍 Direct Job Search")
        
        # Job Search Parameters

        with st.form(key='job_search_form'):
    # Job Search Parameters
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    site_name = st.multiselect(
                        "Select Job Sites", 
                        ["indeed", "linkedin", "zip_recruiter", "glassdoor", "google"], 
                        default=st.session_state.site_name
                    )

                with col2:
                    search_term = st.text_input("Search Term", st.session_state.search_term)
                
                with col3:
                    location = st.text_input("Location", st.session_state.location)
                
                with col4:
                    results_wanted = st.number_input("Number of Results", min_value=1, max_value=100, value=st.session_state.results_wanted)

                # Additional parameters
                col5, col6 = st.columns(2)
                
                with col5:
                    hours_old = st.number_input("Jobs Posted Within (hours)", min_value=1, max_value=168, value=st.session_state.hours_old)

                with col6:
                    country_indeed = st.text_input("Country (for Indeed)", st.session_state.country_indeed)

                # Submit button inside the form
                submit_button = st.form_submit_button("Search Jobs")

                # Only run search when form is submitted
        if submit_button:
            st.session_state.site_name = site_name
            st.session_state.search_term = search_term
            st.session_state.location = location
            st.session_state.results_wanted = results_wanted
            st.session_state.hours_old = hours_old
            st.session_state.country_indeed = country_indeed

            with st.spinner("Searching Jobs..."):
                try:
                    # Your existing job search code here
                    jobs = scrape_jobs(
                        site_name=site_name,
                        search_term=search_term,
                        google_search_term=f"{search_term} jobs near {location}",
                        location=location,
                        results_wanted=results_wanted,
                        hours_old=hours_old,
                        country_indeed=country_indeed,
                    )
                    st.session_state.job_search_results = jobs

                    if len(jobs) > 0:
                        st.success(f"Found {len(jobs)} jobs")
                        
                        jobs_filtered = jobs[['site', 'job_url', 'title', 'company', 'location', 'date_posted']]
                        jobs_filtered['job_url'] = jobs_filtered['job_url'].apply(make_clickable_link)
                        st.write(jobs_filtered.to_html(escape=False), unsafe_allow_html=True)
                        
                        csv_file = jobs.to_csv(index=False)
                        st.download_button(
                            label="Download Jobs as CSV",
                            data=csv_file,
                            file_name='job_search_results.csv',
                            mime='text/csv'
                        )
                    else:
                        st.warning("No jobs found")
                
                except Exception as e:
                    st.error(f"Job Search Error: {e}")
                    logger.error(f"Job Search Error: {e}")
        # col1, col2, col3, col4 = st.columns(4)
        
        # with col1:
        #     site_name = st.multiselect(
        #         "Select Job Sites", 
        #         ["indeed", "linkedin", "zip_recruiter", "glassdoor", "google"], 
        #         default=st.session_state.site_name
        #         # default=["indeed", "glassdoor"]
        #     )
        #     st.session_state.site_name = site_name

        # with col2:
        #     search_term = st.text_input("Search Term", st.session_state.search_term)
        #     st.session_state.search_term = search_term
        
        # with col3:
        #     location = st.text_input("Location", st.session_state.location)
        #     st.session_state.location = location

        
        # with col4:
        #     results_wanted = st.number_input("Number of Results", min_value=1, max_value=100, value=st.session_state.results_wanted)
        #     st.session_state.results_wanted = results_wanted

        # # Additional parameters
        # col5, col6 = st.columns(2)
        
        # with col5:
        #     hours_old = st.number_input("Jobs Posted Within (hours)", min_value=1, max_value=168, value=st.session_state.hours_old)
        #     st.session_state.hours_old = hours_old

        # with col6:
        #     country_indeed = st.text_input("Country (for Indeed)", st.session_state.country_indeed)
        #     st.session_state.country_indeed = country_indeed

        # search_button_clicked = st.button("Search Jobs") 

        # # Search Button
        # # if st.button("Search Jobs"):
        # if search_button_clicked:
        #     with st.spinner("Searching Jobs..."):
        #         # Perform job search
        #         try:
        #             logger.info(f"Performing job search with {search_term} in {location}")
        #             # jobs = scrape_jobs(
        #             #     site_name=site_name,
        #             #     search_term=search_term,
        #             #     google_search_term=f"{search_term} jobs near {location}",
        #             #     location=location,
        #             #     results_wanted=results_wanted,
        #             #     hours_old=hours_old,
        #             #     country_indeed=country_indeed,
        #             # )
        #             jobs = scrape_jobs(
        #                 site_name=st.session_state.site_name,
        #                 search_term=st.session_state.search_term,
        #                 google_search_term=f"{st.session_state.search_term} jobs near {st.session_state.location}",
        #                 location=st.session_state.location,
        #                 results_wanted=st.session_state.results_wanted,
        #                 hours_old=st.session_state.hours_old,
        #                 country_indeed=st.session_state.country_indeed,
        #             )
        #             st.session_state.job_search_results = jobs

        #             if len(jobs) > 0:
        #                 st.success(f"Found {len(jobs)} jobs")
                        
        #                 jobs_filtered = jobs[['site', 'job_url', 'title', 'company', 'location', 'date_posted']]
        #                 # Display job data in a table
        #                 # st.dataframe(jobs)
        #                 jobs_filtered['job_url'] = jobs_filtered['job_url'].apply(make_clickable_link)
        #                 st.write(jobs_filtered.to_html(escape=False), unsafe_allow_html=True)
                        
        #                 # st.dataframe(jobs_filtered)

        #                 # Option to download jobs
        #                 csv_file = jobs.to_csv(index=False)
        #                 st.download_button(
        #                     label="Download Jobs as CSV",
        #                     data=csv_file,
        #                     file_name='job_search_results.csv',
        #                     mime='text/csv'
        #                 )
        #             else:
        #                 st.warning("No jobs found")
                
        #         except Exception as e:
        #             st.error(f"Job Search Error: {e}")
        #             logger.error(f"Job Search Error: {e}")

    

# if __name__ == "__main__":
#     main()