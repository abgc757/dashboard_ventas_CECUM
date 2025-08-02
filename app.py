import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe, get_as_dataframe
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Configuración de Google Sheets
def conectar_google_sheets():
    # Cargar credenciales desde secrets de Streamlit
    creds_dict = st.secrets["gcp_service_account"]
    
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

def cargar_datos():
    client = conectar_google_sheets()
    
    try:
        # Abre la hoja de cálculo por nombre
        spreadsheet = client.open("Datos Inscripciones")
        worksheet = spreadsheet.sheet1
        
        # Carga los datos en un DataFrame
        df = get_as_dataframe(worksheet, evaluate_formulas=True)
        
        # Elimina filas vacías
        df = df.dropna(how='all')
        
        # Procesa las fechas
        if not df.empty:
            df["FECHA DE INSCRIPCION"] = pd.to_datetime(
                df["FECHA DE INSCRIPCION"], dayfirst=True, errors='coerce'
            )
            
            # Calcula año y mes si no existen
            if 'ANIO' not in df.columns:
                df["ANIO"] = df["FECHA DE INSCRIPCION"].dt.year
            if 'MES' not in df.columns:
                df["MES"] = df["FECHA DE INSCRIPCION"].dt.month
        
        return df
    
    except gspread.SpreadsheetNotFound:
        # Si la hoja no existe, crea una nueva
        st.warning("Hoja de cálculo no encontrada. Creando una nueva...")
        spreadsheet = client.create("Datos Inscripciones")
        spreadsheet.share(st.secrets["gcp_service_account"]["client_email"], perm_type='user', role='writer')
        worksheet = spreadsheet.sheet1
        
        # Crea encabezados
        headers = [
            "NO", "FECHA DE INSCRIPCION", "SEMANA", "FECHA DE INICIO CICLO ESCOLAR",
            "MODALIDAD", "ASESOR", "NOMBRE", "NIVEL", "SUBNIVEL", "GRADO", "TURNO",
            "TELEFONO", "MEDIO POR EL CUAL SE ENTERO DE NOSOTROS", "ANIO", "MES"
        ]
        worksheet.append_row(headers)
        
        return pd.DataFrame(columns=headers)

def guardar_datos(df):
    client = conectar_google_sheets()
    
    try:
        spreadsheet = client.open("Datos Inscripciones")
        worksheet = spreadsheet.sheet1
        
        # Actualiza toda la hoja con el DataFrame
        worksheet.clear()
        set_with_dataframe(worksheet, df)
        
        # Ajusta formato de columnas
        worksheet.format('A1:O1', {'textFormat': {'bold': True}})
        
        return True
    except Exception as e:
        st.error(f"Error al guardar en Google Sheets: {e}")
        return False

# ... (código de autenticación existente) ...

# En el formulario, reemplaza la sección de guardado:
if enviar:
    if not nombre or not telefono:
        st.error("Error: Nombre y Teléfono son campos obligatorios")
    else:
        # Cargar datos actuales
        df = cargar_datos()
        
        # Crear nuevo registro
        nuevo_id = df["NO"].max() + 1 if not df.empty and 'NO' in df.columns else 1
        nuevo_registro = {
            "NO": nuevo_id,
            "FECHA DE INSCRIPCION": fecha.strftime("%d/%m/%Y 00:00"),
            "SEMANA": fecha.isocalendar()[1],
            "FECHA DE INICIO CICLO ESCOLAR": ciclo,
            "MODALIDAD": modalidad,
            "ASESOR": asesor,
            "NOMBRE": nombre,
            "NIVEL": nivel,
            "SUBNIVEL": subnivel,
            "GRADO": grado,
            "TURNO": modalidad,
            "TELEFONO": telefono,
            "MEDIO POR EL CUAL SE ENTERO DE NOSOTROS": medio,
            "ANIO": fecha.year,
            "MES": fecha.month
        }

        # Agregar nuevo registro
        nuevo_df = pd.DataFrame([nuevo_registro])
        df = pd.concat([df, nuevo_df], ignore_index=True)
        
        # Guardar en Google Sheets
        if guardar_datos(df):
            st.success("✅ Registro agregado correctamente en Google Sheets!")
            st.balloons()
            
            # Actualizar los datos en session_state
            st.session_state.df = cargar_datos()
        else:
            st.error("❌ Error al guardar el registro")