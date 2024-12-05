import streamlit as st
from typing import Any,Dict
import json
from groq import Groq
import re
import os
import logging

# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)


os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

class ResumeImprovementEngine: 
    def __init__(self):
        # self.llm = ChatGroq(
        #     groq_api_key = groq_api_key,
        #     model_name="llama-3.1-70b-versatile",
        #     temperature=0.7,
        #     max_tokens=4096
        # )
        self.client = Groq(api_key=groq_api_key)
        # logger.info("ResumeImprovementEngine initialized with Groq API key.")

    def generate_resume_improvement_suggestions(self, resume_text: str) -> dict[str, Any]:
            """
            Generate comprehensive resume improvement suggestions
            
            Args:
                resume_text (str): Full text of the resume
            
            Returns:
                Dict containing detailed improvement suggestions
            """
            prompt = f"""Perform a comprehensive analysis of the following resume and provide detailed improvement suggestions:

            Resume Content:
            {resume_text}

            Tasks:
            1. Provide a structured analysis of resume strengths and weaknesses
            2. Offer specific, actionable improvement recommendations
            3. Suggest additional sections or content enhancements
            4. Provide writing and formatting advice
            5. Respond in detailed, structured JSON format

            Required JSON Structure:
            {{
                "overall_assessment": {{
                    "strengths": ["Key strengths of the resume"],
                    "weaknesses": ["Areas needing improvement"]
                }},
                "section_recommendations": {{
                    "work_experience": {{
                        "current_status": "Assessment of current work experience section",
                        "improvement_suggestions": ["Specific improvements"]
                    }},
                    "education": {{
                        "current_status": "Assessment of education section",
                        "improvement_suggestions": ["Specific improvements"]
                    }}
                }},
                "writing_improvements": {{
                    "language_suggestions": ["Writing style improvements"],
                    "formatting_advice": ["Formatting and layout suggestions"]
                }},
                "additional_sections_recommended": ["List of suggested new sections"],
                "keyword_optimization": {{
                    "missing_industry_keywords": ["Keywords to add"],
                    "ats_compatibility_score": "Numeric score or rating"
                }},
                "career_positioning": {{
                    "personal_branding_suggestions": ["Ways to enhance personal brand"],
                    "skill_highlighting_recommendations": ["How to better showcase skills"]
                }}
            }}
            """
            
            try:
                # logger.info("Sending request to Groq for resume improvement.")
                # Make API call to generate improvement suggestions
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are an expert resume consultant providing detailed, constructive feedback."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    model="llama3-groq-70b-8192-tool-use-preview",
                    temperature=0.7,
                    max_tokens=2048,
                    top_p=1,
                    stream=False
                )

                # logger.info("Groq API response received.")
                
                # Extract and parse the JSON response
                response_text = chat_completion.choices[0].message.content
                suggestions = self._extract_json(response_text)

                # logger.debug(f"Improvement suggestions received: {suggestions}")
                
                return suggestions
            
            except Exception as e:
                st.error(f"Resume Improvement Error: {e}")
                # logger.error(f"Resume Improvement Error: {e}")
                return {}
            
    
    def _extract_json(self, text: str) -> dict[str, Any]:
        """
        Safely extract JSON from LLM response
        
        Args:
            text (str): LLM response text
        
        Returns:
            Dict of extracted JSON or empty dict
        """
        try:
            # logger.debug("Extracting JSON from response text.")

            json_match = re.search(r'\{.*\}', text, re.DOTALL | re.MULTILINE)
            if json_match:
                return json.loads(json_match.group(0))
            
            # logger.warning("No valid JSON found in response text.")

            return {}
        
        except Exception as e:
            st.error(f"JSON Extraction Error: {e}")
            # logger.error(f"JSON Extraction Error: {e}")
            return {}
        



# def _extract_json(self, text: str) -> Dict[str, Any]:
    #     """
    #     Safely extract JSON from LLM response with robust error handling
        
    #     Args:
    #         text (str): LLM response text
        
    #     Returns:
    #         Dict of extracted JSON or empty dict
    #     """
    #     try:
    #         logger.debug("Attempting to extract JSON from response text.")
            
    #         # Clean the text and remove any non-JSON characters
    #         # Remove text before first '{' and after last '}'
    #         cleaned_text = text.strip()
    #         first_brace = cleaned_text.find('{')
    #         last_brace = cleaned_text.rfind('}')
            
    #         if first_brace != -1 and last_brace != -1:
    #             cleaned_text = cleaned_text[first_brace:last_brace+1]
            
    #         # Extraction strategies
    #         extraction_strategies = [
    #             # Direct parsing of cleaned text
    #             lambda t: json.loads(t),
                
    #             # Remove non-printable characters and try parsing
    #             lambda t: json.loads(re.sub(r'[^\x20-\x7E\n]', '', t)),
                
    #             # Extract JSON within code block
    #             lambda t: json.loads(re.search(r'```json\n(.*?)```', t, re.DOTALL).group(1) if re.search(r'```json\n(.*?)```', t, re.DOTALL) else '')
    #         ]
            
    #         # Try each extraction strategy
    #         for strategy in extraction_strategies:
    #             try:
    #                 parsed_json = strategy(cleaned_text)
                    
    #                 # Additional validation to ensure it's a dictionary
    #                 if isinstance(parsed_json, dict):
    #                     logger.info("Successfully extracted and parsed JSON.")
    #                     return parsed_json
    #             except (json.JSONDecodeError, AttributeError, IndexError):
    #                 continue
            
    #         # Detailed logging for troubleshooting
    #         logger.warning(f"Could not extract valid JSON. Raw text: {text}")
    #         return {}
        
    #     except Exception as e:
    #         # Log the full error details
    #         logger.error(f"JSON Extraction Error: {e}", exc_info=True)
    #         st.error(f"JSON Extraction Error: {e}")
    #         return {}