import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
import streamlit as st
from fpdf import FPDF
import pandas as pd
import yaml
import time
import os
import io

with open('password/password.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
    hashed_passwords = stauth.Hasher(['admin']).generate()

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, authentication_status, username = authenticator.login('Přihlásit se', 'main')

if authentication_status:

    data_dict = {
        'input_nazev_faktury': None,
        'df': None
    }
    ", clear_on_submit=True"

    st.title('Importování excel tabulky do pdf')
    with st.form("I-form"):
        input_nazev_faktury = st.text_input("Název Faktury")
        uploaded_file = st.file_uploader('Vložte prosím soubor Excel.', type='xlsx')

        if st.form_submit_button("Uložit"):
            if input_nazev_faktury.strip() == "":
                warning_message = st.warning("Název faktury nesmí být prázdný.")
                time.sleep(2)
                warning_message.empty()
            elif uploaded_file is None:
                warning_message = st.warning("Nebyl nahrán žádný soubor. Vložte soubor pro pokračování.")
                time.sleep(2)
                warning_message.empty()
            else:
                df = pd.read_excel(uploaded_file, engine='openpyxl')
                df['Celková cena'] = df['Ks'] * df['Cena ks']
                df['Název faktury'] = input_nazev_faktury

                data_dict['input_nazev_faktury'] = input_nazev_faktury
                data_dict['df'] = df

    if data_dict['df'] is not None:
        pdf = FPDF(format='A4')
        pdf.add_page()
        pdf.add_font("DejaVu", "", "font/dejavu-fonts-ttf-2.37/ttf/DejaVuSansCondensed.ttf", uni=True)
        pdf.set_font("DejaVu", size=12)

        pdf.cell(200, 10, f"Faktura {data_dict['input_nazev_faktury']}", ln=True, align='C')
        pdf.ln(10)

        pdf_output = io.BytesIO(pdf.output(dest="S"))
        st.subheader("Stáhnout PDF:")
        st.download_button(
            label="Stáhnout PDF", 
            data=pdf_output,
            file_name=f"{data_dict['input_nazev_faktury']}.pdf",
            key="download-pdf"
        )

    data = {
        "Popis": ["", "", ""],
        "Ks": ["", "", ""],
        "Cena ks": ["", "", ""]
    }

    empty_df = pd.DataFrame(data)

    excel_folder_path = "excel_template/"
    if not os.path.exists(excel_folder_path):
        os.makedirs(excel_folder_path)

    st.subheader('Stáhnout template:')
    temp_excel_file_path = os.path.join(excel_folder_path, "template.xlsx")
        
    empty_df.to_excel(temp_excel_file_path, index=False)

    st.download_button(
        label="Stáhnout Excel soubor",
        data=temp_excel_file_path,
        file_name="template.xlsx",
        key="excel-download"
    )

    authenticator.logout('Logout', 'main', key='unique_key')

elif authentication_status is False:
    error_message = st.error('Uživatelské jméno/heslo je nesprávné')
    time.sleep(2)
    error_message.empty()

elif authentication_status is None:
    warning_message = st.warning('Zadejte prosím své uživatelské jméno a heslo.')
    time.sleep(2)
    warning_message.empty()