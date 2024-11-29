
"""
        Simple Working Version Of Job_Spy in Streamlit
"""

import csv
from jobspy import scrape_jobs
import streamlit as st
import pandas as pd

st.title("Job-Scrapper")

site_name = st.multiselect(
    "Select Job Sites", ["indeed", "linkedin", "zip_recruiter", "glassdoor", "google"], default=["indeed", "linkedin"]
)

search_term = st.text_input("Search Term", "software engineer")
location = st.text_input("Location", "San Francisco, CA")
results_wanted = st.number_input("Number of Results", min_value=1, max_value=100, value=20)
hours_old = st.number_input("How many hours old?", min_value=1, max_value=168, value=72)
country_indeed = st.text_input("Country (for Indeed)", "USA")

if st.button("scrape jobs"):
    jobs = scrape_jobs(
        site_name=site_name,
        search_term=search_term,
        google_search_term= f"{search_term} jobs near {location}",
        location=location,
        results_wanted= results_wanted,
        hours_old=hours_old,
        country_indeed=country_indeed,
        
        # linkedin_fetch_description=True # gets more info such as description, direct job url (slower)
        # proxies=["208.195.175.46:65095", "208.195.175.45:65095", "localhost"],
    )

    if len(jobs) > 0:
        st.success(f"Found {len(jobs)} jobs")
        
        # Display job data in a table
        st.dataframe(jobs)

    else:
        st.warning("No jobs found")
# print(f"Found {len(jobs)} jobs")
# print(jobs.head())
# jobs.to_csv("jobs.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False) # to_excel
