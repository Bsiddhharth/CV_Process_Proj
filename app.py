
import streamlit as st
import cv_question
import cv_short
import cv_analyzer_search
from logger import setup_logger

# def initialize_session_state():
    # """Initialize all session state variables with default values."""
    # session_vars = {
    #     'jd_text': "",
    #     'min_years': 0,
    #     'required_skills_list': [],
    #     'uploaded_files': [],
    #     'results': [],
    #     'generated_questions': None,
    #     'current_candidate_index': 0,
    #     'processed_cvs': {},  # Store processed CV data
    #     'analysis_complete': False
    # }
    
    # for var, default_value in session_vars.items():
    #     if var not in st.session_state:
    #         st.session_state[var] = default_value

def clear_session_state():
    """Clear all session state variables."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    # initialize_session_state()
    
def main():
    # Setup logger for app
    app_logger = setup_logger('app_logger', 'app.log')
    
    # initialize_session_state()
    
    # Sidebar
    st.sidebar.title("Navigation")
    app_logger.info("Sidebar navigation displayed")
    
    # Add reset button in sidebar
    if st.sidebar.button("Reset All Data"):
        clear_session_state()
        st.sidebar.success("All data has been reset!")
        app_logger.info("Session state reset")
    
    # Navigation
    page = st.sidebar.radio("Go to", ["CV Shortlisting", "Interview Questions","CV Analyser + JobSearch"])
    app_logger.info(f"Page selected: {page}")
    
    try:
        if page == "CV Shortlisting":
            app_logger.info("Navigating to CV Shortlisting")
            cv_short.create_cv_shortlisting_page()
            
        elif page == "Interview Questions":
            # Check if CV shortlisting is complete
            # if not st.session_state.analysis_complete:
            #     st.warning("Please complete the CV shortlisting process first.")
            #     app_logger.warning("Attempted to access Interview Questions without completing CV shortlisting")
            # else:
                app_logger.info("Navigating to Interview Questions")
                cv_question.create_interview_questions_page()

        elif page == "CV Analyser + JobSearch":
            cv_analyzer_search.Job_assistant()
                
    except Exception as e:
        app_logger.error(f"Error occurred: {e}")
        st.error(f"An error occurred: {e}")
        
if __name__ == "__main__":
    main()
