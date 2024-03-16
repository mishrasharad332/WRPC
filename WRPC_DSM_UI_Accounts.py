from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Color
from openpyxl.styles.colors import BLUE
from datetime import datetime
import streamlit as st
import pandas as pd
import requests
import fitz  # For PDF processing
import os
import re
import streamlit as st
import io  # Import io module
import pdfplumber  # Alternative library for PDF processing

selected_pdf = []
search_text = "Arinsun_RUMS"

def create_file(df, sheet_name):
    filename = f"Extracted Data_WRPC_SRPC_{datetime.now().strftime('%d-%m-%Y')}.xlsx"

    # Check file existence
    if not os.path.exists(filename):
        wb = Workbook()
        wb.save(filename)
    else:
        wb = load_workbook(filename)

    # Check if sheet exists
    if sheet_name not in wb.sheetnames:
        wb.create_sheet(title=sheet_name)
    ws2 = wb[sheet_name]

    # Write specific column names as headers
    headers = ['Date', 'Entity', 'Injection', 'Schedule', 'DSM Payable', 'DSM Receivable', 'Net DMC', 'PDF URL']
    ws2.append(headers)

    # Append data to the worksheet
    for index, row in df.iterrows():  # Iterate over DataFrame rows
        # Split the 'PDF URL' column into two separate columns for hyperlink function
        # row["PDF URL"] = row["PDF URL"].split(", ")[1].strip(')')
        row_list = row.to_list()  # Convert DataFrame row to a list
        ws2.append(row_list)  # Append the row to the worksheet

    # Save the workbook
    wb.save(filename)

def create_dataframe(financial_data):
    if not financial_data:
        print("No financial data available.")
        return None

    # Extracted financial data
    entity_name = search_text
    payable = financial_data[0]
    receivable = financial_data[1]
    net_dsm = financial_data[2]
    payable_receivable = financial_data[3]

    # Create DataFrame
    df = pd.DataFrame({
        "Name Of Entity": [entity_name],
        "Payable": [payable],
        "Receivable": [receivable],
        "Net DSM(Rs.)": [net_dsm],
        "Payable/Receivable": [payable_receivable]
    })
    return df

def extract_text_from_pdf(pdf_url):
    try:
        # Download the PDF file
        pdf_data = requests.get(pdf_url).content

        # Load the PDF data
        pdf = pdfplumber.open(io.BytesIO(pdf_data))

        # Extract text from each page
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

# Function to fetch PDFs
def fetch_pdfs(year, title_filter):
    wrpc_base_url = "https://www.wrpc.gov.in"
    search_text = "Arinsun_RUMS"
    UI_link = wrpc_base_url + "/assets/data/UI_" + year + '.txt'
    session_state = st.session_state

    if 'checkbox_values' not in session_state:
        session_state.checkbox_values = {}

    response = requests.get(UI_link)

    ui_data = ""
    pdf_links = []
    titles = []
    url_data= {}
    
    if response.status_code == 200:
        ui_data = response.text

    lines = ui_data.split("\n")
    session_state = st.session_state

    for line in lines[1:]:
        parts = line.split(",")
        
        if len(parts) == 5:
            from_date, to_date, link, issue_date, status = parts
            week = re.search(r'week=([\w.]+)', link).group(1)
            yy = re.search(r'yy=(\w+)', link).group(1)
            potential_month = yy.lower()[:3]

            filtered_month = (title_filter.lower().startswith(potential_month) and title_filter) or None

            if filtered_month:
                pdf_link = f"https://www.wrpc.gov.in/htm/{yy}/sum{week}.pdf"
                pdf_links.append(pdf_link)

                status_text = "Revised" if status.strip() == "R" else "Issued"
                output = f"Week{week}: {from_date} to {to_date}\n({status_text} on {issue_date})"
                titles.append(output)

    checkbox_values = []
    url_data = dict(zip(titles, pdf_links))

    checkbox_values = {url: st.checkbox(f"{title}: {url}") for url, title in url_data.items()}
    
    if st.button("Continue"):
        for url, checked in checkbox_values.items():
            selected_pdf.append(url_data[url])

        table_data = []

        for pdf_url in selected_pdf:
            print(pdf_url)

            extracted_text = extract_text_from_pdf(pdf_url)

            # Check if extracted text is bytes-like object and decode it to string
            if isinstance(extracted_text, bytes):
                extracted_text = extracted_text.decode("utf-8")

            pattern_combined = re.compile(r'(\d{2}-\w{3}|Total)\s(Arinsun_RUMS)\s(\d+\.\d+)\s(\d+\.\d+)\s?(\d+\.\d+)?\s?(\d+\.\d+)?\s?(\-?\d+\.\d+)?')

            matches = pattern_combined.findall(extracted_text)

            headers = ['Date', 'Entity', 'Injection', 'Schedule', 'DSM Payable', 'DSM Receivable', 'Net DMC']

            structured_data = []

            for match in matches:
                row_dict = dict(zip(headers, match))
                row_dict['PDF URL'] = pdf_url
                structured_data.append(row_dict)

            table_data.extend(structured_data)

        df = pd.DataFrame(table_data)
        st.write(df)

        sheet_name = 'WRPC_DSM'
        create_file(df, sheet_name)

if __name__ == '__main__':
    st.markdown('### WRPC DSM UI ACCOUNTS')
    years = ['2023', '2022', '2021', '2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012', '2011', '2010']
    selected_year = st.selectbox('Select a Year:', years)  

    months = ["January", "February", "March", "April","May", "June", "July", "August","September", "October", "November", "December"] 
    selected_month = st.selectbox("Select a month", options=months, index=0, format_func=lambda x: x.title())
    st.write("Please select at least one pdf before continue")
    fetch_pdfs(selected_year, selected_month)
 
    print("Done")
