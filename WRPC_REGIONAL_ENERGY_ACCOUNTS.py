from datetime import datetime
from openpyxl.styles import Font, Color
import streamlit as st
import pandas as pd
import requests
import fitz  # For PDF processing
import os
import re

# Function to fetch PDFs
def fetch_pdfs(year, title_filter):
    
    wrpc_base_url = "https://www.wrpc.gov.in"
    search_text = "Arinsun_RUMS"
    UI_link = wrpc_base_url + "/assets/data/UI_" + year + '.txt'
    # Create a session state object
    session_state = st.session_state

    # Check if checkbox values exist in session state
    if 'checkbox_values' not in session_state:
        session_state.checkbox_values = {}

    # Make the GET request
    response = requests.get(UI_link)

    ui_data = ""
    pdf_links = []
    chckbox_headers = []

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        ui_data = response.text     # Split the response text by lines

    # Split the response by lines
    lines = ui_data.split("\n")
    session_state = st.session_state

    # Iterate through each line and process the data, skipping the header
    for line in lines[1:]:
        # Split the line by commas
        parts = line.split(",")
        
        if len(parts) == 5:
            from_date, to_date, link, issue_date, status = parts
            # Extract "week" and "yy" values from the link
            week = re.search(r'week=([\w.]+)', link).group(1)
            yy = re.search(r'yy=(\w+)', link).group(1)
            potential_month = yy.lower()[:3]  # Extract first 3 characters (potential month abbreviation)

            # Comparison and filtering
            filtered_month = (title_filter.lower().startswith(potential_month) and title_filter) or None

            if filtered_month:
                # Construct the PDF link
                pdf_link = f"https://www.wrpc.gov.in/htm/{yy}/sum{week}.pdf"
                pdf_links.append(pdf_link)

                # Determine the status text
                status_text = "Revised" if status.strip() == "R" else "Issued"
                # Construct the output string
                output = f"Week{week}: {from_date} to {to_date}\n({status_text} on {issue_date})"
                st.markdown(f"**{output}**")

                # st.session_state[pdf_link] = False  # Initialize with default value
                st.checkbox(pdf_link)
    
    
    checkbox_values = []

    if st.button("Continue"):
        for label in pdf_links:
            checkbox_values.append(st.checkbox(label))

        for label, value in zip(pdf_links, checkbox_values):
            st.write(f"{label}: {value}")

    # if st.button("Continue"):
    #     for label in pdf_links:
    #         checkbox_values.append(st.checkbox(label))

        # for label, value in zip(pdf_links, checkbox_values):
        #     st.write(f"{label}: {value}")


if __name__ == '__main__':
    st.markdown('### WRPC DSM UI ACCOUNTS')
    years = ['2023', '2022', '2021', '2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012', '2011', '2010']
    selected_year = st.selectbox('Select a Year:', years)  

    months = ["January", "February", "March", "April","May", "June", "July", "August","September", "October", "November", "December"] 
    selected_month = st.selectbox("Select a month", options=months, index=0, format_func=lambda x: x.title())
    
    fetch_pdfs(selected_year, selected_month)
    # if st.button('Extract Data'): 
