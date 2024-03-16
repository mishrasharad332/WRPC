from openpyxl.styles import Font, Color
from openpyxl.styles.colors import BLUE
from datetime import datetime
from openpyxl.styles import Font, Color
import streamlit as st
import pandas as pd
import requests
import fitz  # For PDF processing
import os
import re

selected_pdf = []
search_text = "Arinsun_RUMS"

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

def extract_financial_data(text, search_text="Arinsun_RUMS", num_lines=4):
    try:
        # Find the index of the first occurrence of the search text
        start_index = text.find(search_text)
        if start_index == -1:
            print(f"Search text '{search_text}' not found.")
            return None, -1

        # Split the text into lines
        lines = text.split("\n")

        # Find the index of the line containing the search text
        line_index = [i for i, line in enumerate(lines) if search_text in line][0]

        # Extract the lines below the first occurrence of the search text
        data_lines = lines[line_index + 1 : line_index + 1 + num_lines]

        print(data_lines)

        # Process the data lines
        financial_data = [line.strip() for line in data_lines]

        return financial_data, line_index
    except Exception as e:
        print(f"Error extracting financial data: {e}")
        return None, -1

def extract_text_from_pdf(pdf_url):
    try:
        # Download the PDF file
        pdf_data = requests.get(pdf_url).content

        # Load the PDF data
        pdf_document = fitz.open(stream=pdf_data, filetype="pdf")

        # Extract text from each page
        text = ''
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None
    
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
    titles = []
    url_data= {}
    
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
                titles.append(output)
   

    checkbox_values = []
    url_data = dict(zip(titles, pdf_links))

    checkbox_values = {url: st.checkbox(f"{title}: {url}") for url, title in url_data.items()}
    
    # Button to continue
    
    if st.button("Continue"):
        for url, checked in checkbox_values.items():
            # st.write(f"Title: {url_data[url]}, URL: {url}, Checked: {checked}")
            selected_pdf.append(url_data[url])

        # if st.button('Extract Data'):
            
        table_data = []

        for pdf_url in selected_pdf:
            print(pdf_url)

            # Extract text from the PDF
            extracted_text = extract_text_from_pdf(pdf_url)

            # Define the pattern to extract the headers and data rows
            pattern_combined = re.compile(r'(\d{2}-\w{3}|Total)\s(Arinsun_RUMS)\s(\d+\.\d+)\s(\d+\.\d+)\s?(\d+\.\d+)?\s?(\d+\.\d+)?\s?(\-?\d+\.\d+)?')

            # Find all matches in the text
            matches = pattern_combined.findall(extracted_text)

            # Define headers
            headers = ['Date', 'Entity', 'Injection', 'Schedule', 'DSM Payable', 'DSM Receivable', 'Net DMC']

            # Initialize a list to store the structured data
            structured_data = []

            # Iterate over matches and create dictionaries for each row
            for match in matches:
                row_dict = dict(zip(headers, match))
                row_dict['PDF URL'] = pdf_url  # Add pdf_url to the row dictionary
                structured_data.append(row_dict)

            # Append the structured data to the table_data list
            table_data.extend(structured_data)

        df = pd.DataFrame(table_data)
        st.write(df)

        filename = f"Extracted Data_WRPC_SRPC_{datetime.now().strftime('%d-%m-%Y')}.xlsx"
        sheet_name = 'WRPC_DSM'

        # Check file existence and handle sheet existence
        if not os.path.exists(filename):
            # Create the file and write the DataFrame
            writer = pd.ExcelWriter(filename, engine='openpyxl')
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        else:
            # Append data to the existing file, handling sheet existence
            writer = pd.ExcelWriter(filename, engine='openpyxl', mode='a', if_sheet_exists='overlay')  # Key change here

            # Get the starting row for appending (ensuring sheet exists)
            startrow = writer.sheets[sheet_name].max_row

            # Append the DataFrame
            df.to_excel(writer, sheet_name=sheet_name, startrow=startrow, index=False, header=False)

        st.write(f"\nSaving to '{filename}'->'{sheet_name}'")
        # Get the workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # Set the hyperlink color to blue
        font_blue = Font(color=Color(rgb=BLUE))
        for cell in worksheet['F']:
                cell.font = font_blue
        writer.close()

if __name__ == '__main__':
    st.markdown('### WRPC DSM UI ACCOUNTS')
    years = ['2023', '2022', '2021', '2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012', '2011', '2010']
    selected_year = st.selectbox('Select a Year:', years)  

    months = ["January", "February", "March", "April","May", "June", "July", "August","September", "October", "November", "December"] 
    selected_month = st.selectbox("Select a month", options=months, index=0, format_func=lambda x: x.title())
    st.write("Please select at least one pdf before continue")
    fetch_pdfs(selected_year, selected_month)
    # if st.button('Extract Data'): 

    # if st.button('Extract Data'):
        