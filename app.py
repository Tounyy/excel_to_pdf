import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
import streamlit as st
from fpdf import FPDF
import pandas as pd
import datetime
import yaml
import time
import os

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

    st.title('Importování excel tabulky do pdf')
    with st.form("I-form"):
        input_nazev_faktury = st.text_input("Zadejte prosím číslo dodacího listu")
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
                data_dict['input_nazev_faktury'] = input_nazev_faktury
                data_dict['df'] = df
    
    if data_dict['df'] is not None:
        aktualni_datum = datetime.datetime.now().strftime("%Y-%m-%d")
        pdf = FPDF(format='A4')
        pdf.add_page()
        pdf.add_font("DejaVu", "", "font/dejavu-fonts-ttf-2.37/ttf/DejaVuSansCondensed.ttf", uni=True)
        pdf.set_font("DejaVu", size=12)
        col_width = 40  

        pdf.set_text_color(30, 30, 30) 
        pdf.set_font("DejaVu", size=14)
        pdf.cell(0, 10, f"Dodací list č. {data_dict['input_nazev_faktury']}", ln=True, align='L') 
        pdf.ln(10)

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("DejaVu", size=9)
        pdf.set_xy(10, 26) 
        text_block1 = "Hammer Masters s.r.o.\nU Vodárny 1081/2\n530 09 Pardubice\nČeská republika\nSpolečnost zapsal do OR Krajský\nsoud v Hradci Králové pod spisovou\nznačkou C 1111.\nIČO: 83125649\nDIČ: CZ83125649\nPlátce DPH\nTELEFON: +420 (466) 2200 0001\nEMAIL: info@hammermasters.cz\n"
        pdf.multi_cell(100, 7, text_block1, align='L')

        pdf.set_font("DejaVu", size=9)
        pdf.set_xy(130, 25.5)  
        text_block2 = f"Odběratel:\nBytový komplex Slunečná zahrada, s.r.o.\nKvětnová 781/15\n140 00 Praha 4\nČeská republika\nDodací adresa:\nBytový komplex Slunečná zahrada\nU Slunečního vršku 837\n140 00 Praha 4\nDatum vystavení {aktualni_datum}"
        pdf.multi_cell(100, 7, text_block2, align='L')

        pdf.ln(20)
        pdf.set_draw_color(0, 0, 0)  
        pdf.line(10, pdf.get_y(), 190 + 10, pdf.get_y()) 
        pdf.ln(5)

        col_width = pdf.w / 4
        row_height = pdf.font_size

        pdf.set_font("DejaVu", size=10)
        column_width = 40
        column_spacing = 5
        row_spacing = 3

        column_spacing_others = 2  # Default spacing for other columns
        column_spacing_kss = 2  # Spacing for the "Ks" column
        column_spacing_cena_kss = 2  # Spacing for the "Cena ks" column
        column_spacing_celkova_cenas = 2  # Spacing for the "Celková cena" column

        for column_name in data_dict['df'].columns:
            if column_name == "Popis":
                column_width = 70
                align = 'L'  # Nastavte zarovnání na levý okraj pro sloupec "Popis"
            elif column_name == "Ks":
                column_width = 30
                column_spacing = column_spacing_kss
                align = 'R'
            elif column_name == "Cena ks":
                column_width = 35
                column_spacing = column_spacing_cena_kss
                align = 'R'
            elif column_name == "Celková cena":
                column_width = 40
                column_spacing = column_spacing_celkova_cenas
                align = 'R'
            else:
                column_spacing = column_spacing_others
                align = 'R'
            
            pdf.cell(column_width, row_height, column_name, border=0, align=align)  # Nastavte zarovnání
            pdf.cell(column_spacing)
        pdf.ln(row_height)
        pdf.ln(3)

        # Vytvořte seznam řádků pro PDF
        pdf_rows = []

        # Nastavte menší výšku řádku
        smaller_row_height = 2.3  # Změňte podle potřeby

        for index, row in data_dict['df'].iterrows():
            # Předpokládáme, že sloupec "Popis" je nejdelší
            popis_value = row['Popis']
            if len(str(popis_value)) > 46:
                parts = [popis_value[i:i+46] for i in range(0, len(popis_value), 46)]
                # Přidáme prázdné řádky pro popis, aby se zachovala výška pro ostatní sloupce
                max_rows = len(parts)
                for i in range(max_rows):
                    pdf_row = []
                    for column_name in data_dict['df'].columns:
                        if column_name == 'Popis':
                            if i < len(parts):
                                # Přidáme pomlčku na konec řádku, pokud to není poslední řádek
                                if i == max_rows - 1:
                                    pdf_row.append(parts[i])
                                else:
                                    pdf_row.append(parts[i] + "-")
                            else:
                                pdf_row.append("")  # Prázdný řádek po dokončení textu
                        else:
                            if i == 0:
                                # Přidáme data z ostatních sloupců pouze pro první řádek popisu
                                cell_value = row[column_name]
                                try:
                                    float_value = float(cell_value)
                                    formatted_value = "{:,.2f}".format(float_value)
                                    pdf_row.append(formatted_value)
                                except ValueError:
                                    pdf_row.append(cell_value)
                            else:
                                pdf_row.append("")  # Prázdný řádek pro ostatní sloupce
                    pdf_rows.append(pdf_row)
            else:
                pdf_row = []
                for column_name in data_dict['df'].columns:
                    if column_name == 'Popis':
                        pdf_row.append(popis_value)
                    else:
                        cell_value = row[column_name]
                        try:
                            float_value = float(cell_value)
                            formatted_value = "{:,.2f}".format(float_value)
                            pdf_row.append(formatted_value)
                        except ValueError:
                            pdf_row.append(cell_value)
                pdf_rows.append(pdf_row)
                
        # Nyní použijte seznam řádků pro vytvoření PDF s menší výškou řádku
        for pdf_row in pdf_rows:
            for i, cell_value in enumerate(pdf_row):
                if i == 0:  # První sloupec (Popis)
                    pdf.cell(column_width + 30, smaller_row_height, cell_value, border=0, align='L')
                    pdf.cell(column_spacing - 10)
                elif i == 1:  
                    pdf.cell(column_width + 3, smaller_row_height, cell_value, border=0, align='R')
                    pdf.cell(column_spacing - 10)
                elif i == 2:  
                    pdf.cell(column_width + 5, smaller_row_height, cell_value, border=0, align='R')
                    pdf.cell(column_spacing - 9)
                else:
                    pdf.cell(column_width + 9, smaller_row_height, cell_value, border=0, align='R')
                    pdf.cell(column_spacing - 15)
            pdf.ln(smaller_row_height) 
            pdf.ln(row_spacing)

        pdf.ln(1)
        pdf.set_draw_color(0, 0, 0)  
        pdf.line(10, pdf.get_y(), 190 + 10, pdf.get_y()) 
        pdf.ln(1.50)

        pdf.cell(column_width + 30, row_height, "Celková cena", border=0,  align='L')
        pdf.cell(column_width, row_height, "", border=0)  
        pdf.cell(column_width, row_height, "", border=0)  
        total_price = df['Celková cena'].sum()
        formatted_sum = "{:,.2f}".format(total_price)
        pdf.cell(column_width - 6.05, row_height, formatted_sum, border=0, align='R')

        pdf_output = pdf.output(dest="S").encode("latin1")
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
        "Cena": ["", "", ""]
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