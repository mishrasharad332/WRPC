import streamlit as st

# Sample data
checkbox_labels = ['https://www.wrpc.gov.in/htm/jan23/sum5.pdf', 'https://www.wrpc.gov.in/htm/jan23/sum4.pdf', 'https://www.wrpc.gov.in/htm/jan23/sum3.a.pdf', 'https://www.wrpc.gov.in/htm/jan23/sum3.pdf', 'https://www.wrpc.gov.in/htm/jan23/sum2.pdf', 'https://www.wrpc.gov.in/htm/jan23/sum1.pdf']

# Create multiple checkboxes
checkbox_values = [st.checkbox(label) for label in checkbox_labels]

# Button to print checkbox values
if st.button("Print Checkbox Values"):
    for label, value in zip(checkbox_labels, checkbox_values):
        st.write(f"{label}: {value}")
