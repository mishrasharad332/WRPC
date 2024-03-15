from datetime import datetime
from IPython.display import display, HTML
from openpyxl.styles import Font, Color
from openpyxl.styles.colors import BLUE
from ipywidgets import widgets
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

    # Make the GET request
    response = requests.get(UI_link)

    ui_data = ''
    checkboxes=[]

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Split the response text by lines
        ui_data = response.text

    # Split the response by lines
    lines = ui_data.split("\n")

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

                # Determine the status text
                status_text = "Revised" if status.strip() == "R" else "Issued"

                # Construct the output string
                output = f"Week{week}: {from_date} to {to_date}\n({status_text} on {issue_date})"

                st.markdown(f"**{output}**")

                checkbox = st.checkbox(pdf_link, value=False)
                checkboxes.append(checkbox)

    if st.button("Download Selected PDFs"):
        selected_pdf_links = [f for c, f in zip(checkboxes, [f"https://www.wrpc.gov.in/htm/{yy}/sum{week}.pdf" for yy, week in zip(yy_list, week_list)]) if c]
        for link in selected_pdf_links:
            st.markdown(f"Downloading {link}...")
    
    selected_links=[]
    
    # Function to update selected PDF links
    def update_selected_links(checkboxes):
        # selected_links.clear()
        for checkbox in checkboxes:
            if checkbox:
                selected_links.append(checkbox)

    # Observe changes in checkbox values and update selected PDF links
    update_selected_links(checkboxes)

    # Display the selected PDF links
    # if st.button("Show Selected PDFs", key="show_button"):
    #     st.write("Selected PDF Links:")
    #     for link in selected_links:
    #         st.write(link)

if __name__ == '__main__':

    st.markdown('### WRPC DSM UI ACCOUNTS')
    years = ['2023', '2022', '2021', '2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012', '2011', '2010']
    selected_year = st.selectbox('Select a Year:', years)  

    months = ["January", "February", "March", "April","May", "June", "July", "August","September", "October", "November", "December"] 
    selected_month = st.selectbox("Select a month", options=months, index=0, format_func=lambda x: x.title())
    
    if st.button('Extract Data'):
        fetch_pdfs(selected_year, selected_month)