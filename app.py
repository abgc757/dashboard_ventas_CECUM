import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe, get_as_dataframe

# --- Configuración de Google Sheets ---
def conectar_google_sheets():
    # Cargar credenciales desde secrets de Streamlit
    creds_dict = st.secrets["gcp_service_account"]
    
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

# Función para cargar datos desde Google Sheets
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
        if not df.empty and "FECHA DE INSCRIPCION" in df.columns:
            # Convertir cualquier formato a datetime
            df["FECHA DE INSCRIPCION"] = pd.to_datetime(
                df["FECHA DE INSCRIPCION"], 
                dayfirst=True, 
                errors='coerce',
                format='mixed'  # Acepta múltiples formatos
            )
            # Calcular año y mes
            df["ANIO"] = df["FECHA DE INSCRIPCION"].dt.year
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

# Función para guardar datos en Google Sheets
def guardar_datos(df):
    client = conectar_google_sheets()
    
    try:
        spreadsheet = client.open("Datos Inscripciones")
        worksheet = spreadsheet.sheet1
        
        # Convertir fechas a formato DD/MM/YYYY antes de guardar
        if not df.empty and "FECHA DE INSCRIPCION" in df.columns:
            # SOLUCIÓN: Convertir primero a datetime y luego formatear
            df["FECHA DE INSCRIPCION"] = pd.to_datetime(
                df["FECHA DE INSCRIPCION"], 
                errors='coerce'
            ).dt.strftime("%d/%m/%Y")
        
        # Actualiza toda la hoja con el DataFrame
        worksheet.clear()
        set_with_dataframe(worksheet, df)
        
        # Ajusta formato de columnas
        worksheet.format('A1:O1', {'textFormat': {'bold': True}})
        
        return True
    except Exception as e:
        st.error(f"Error al guardar en Google Sheets: {e}")
        return False

try:
    # Cargar configuración
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    # Autenticación
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
    )
    
    # Login form
    name, authentication_status, username = authenticator.login("Login", "main")
    
    # Manejar estados de autenticación
    if authentication_status is False:
        st.error("Usuario o contraseña incorrectos")
        st.stop()
    elif authentication_status is None:
        st.warning("Por favor inicia sesión")
        st.stop()
    
    # Mostrar contenido si está autenticado
    authenticator.logout("Cerrar sesión", "sidebar")
    st.sidebar.success(f"Bienvenido, {name}")
    
    # Obtener permisos del usuario
    permisos_usuario = config['credentials']['usernames'][username].get('permisos', [])
    st.session_state['permisos'] = permisos_usuario

except KeyError as e:
    st.error(f"Error en configuración: Falta la clave {e} en config.yaml")
    st.stop()
except FileNotFoundError:
    st.error("Archivo config.yaml no encontrado")
    st.stop()
except Exception as e:
    st.error(f"Error inesperado: {str(e)}")
    st.stop()

# Diccionario de meses en español a números
meses = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4,
    "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
    "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
}

def convertir_fecha(texto):
    try:
        partes = texto.strip().upper().split(" DE ")
        mes = meses.get(partes[0], 1)
        año = int("20" + partes[1]) if len(partes) > 1 else datetime.today().year
        return pd.Timestamp(day=1, month=mes, year=año)
    except:
        return pd.NaT

# Inicializar datos en session_state
if 'df' not in st.session_state:
    st.session_state.df = cargar_datos()

# Obtener datos actualizados
df = st.session_state.df

hoy = datetime.today().date()
ayer = hoy - timedelta(days=1)
año_actual = hoy.year
año_pasado = año_actual - 1

# Título
st.markdown(f"<h1 style='text-align: center;'>📊 Dashboard Campaña de ventas {año_actual}</h1>", 
            unsafe_allow_html=True)

# Métricas principales
col1, col2, col3 = st.columns(3)
with col1:
    total_actual = len(df[df["ANIO"] == año_actual])
    st.metric("Total de inscritos", total_actual)

with col2:
    # Asegurar que la fecha sea comparable
    if not df.empty and "FECHA DE INSCRIPCION" in df.columns:
        df["FECHA_DATE"] = pd.to_datetime(df["FECHA DE INSCRIPCION"]).dt.date
        inscritos_ayer = len(df[df["FECHA_DATE"] == ayer])
    else:
        inscritos_ayer = 0
    st.metric("Inscritos ayer", inscritos_ayer)

with col3:
    total_pasado = len(df[df["ANIO"] == año_pasado])
    avance = (total_actual / total_pasado * 100) if total_pasado > 0 else 0
    st.metric(f"% Avance vs {año_pasado}", f"{avance:.2f}%")

# Gráfico de avance por nivel académico
st.subheader(f"📈 Avance por Nivel Académico vs {año_pasado}")
niveles = sorted(df['NIVEL'].dropna().unique())

# Manejo de datos faltantes
anio_actual_data = df[df['ANIO'] == año_actual]['NIVEL'].value_counts().reindex(niveles, fill_value=0)
anio_pasado_data = df[df['ANIO'] == año_pasado]['NIVEL'].value_counts().reindex(niveles, fill_value=0)

# Calcular avance seguro
avance = []
for i in range(len(niveles)):
    actual = anio_actual_data.iloc[i]
    pasado = anio_pasado_data.iloc[i]
    if pasado > 0:
        avance.append(f"{(actual/pasado*100):.1f}%")
    else:
        avance.append("Nuevo" if actual > 0 else "0%")

# Mostrar en columnas
col1, col2 = st.columns(2)
with col1:
    # Gráfico mejorado
    chart_data = pd.DataFrame({
        año_pasado: anio_pasado_data.values,
        año_actual: anio_actual_data.values
    }, index=niveles)
    st.bar_chart(chart_data)

with col2:
    # Tabla con estilo
    st.dataframe(
        pd.DataFrame({
            "Nivel": niveles,
            año_pasado: anio_pasado_data.values,
            año_actual: anio_actual_data.values,
            "% Avance": avance
        }).style.format({
            año_pasado: '{:,.0f}',
            año_actual: '{:,.0f}'
        }),
        hide_index=True
    )

# Gráfico por escuela
st.subheader("🏫 Inscritos por escuela")
niveles_disponibles = sorted(df["NIVEL"].dropna().unique())
nivel_seleccionado = st.selectbox("Selecciona un nivel académico", 
                                  ["Todos"] + niveles_disponibles,
                                  key='nivel_selector')

if nivel_seleccionado == "Todos":
    datos_filtrados = df[df["ANIO"] == año_actual]
else:
    datos_filtrados = df[(df["ANIO"] == año_actual) & (df["NIVEL"] == nivel_seleccionado)]

if not datos_filtrados.empty:
    grado_count = datos_filtrados["SUBNIVEL"].value_counts()
    st.bar_chart(grado_count)
else:
    st.warning("No hay datos para el nivel seleccionado")

# Gráficos en columnas
col1, col2 = st.columns(2)
with col1:
    st.subheader("👩‍🏫 Inscritos por Asesor")
    # Usar columna ANIO para filtrar
    asesor_count = df[df["ANIO"] == año_actual]["ASESOR"].value_counts()
    st.bar_chart(asesor_count)

with col2:
    st.subheader("🎓 Inscritos por Nivel")
    nivel_count = df[df["ANIO"] == año_actual]["NIVEL"].value_counts()
    st.bar_chart(nivel_count)

# Histórico mensual
st.subheader(f"📊 Histórico mensual {año_actual} vs {año_pasado}")

# Crear un DataFrame completo con todos los meses en orden
nombres_meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
meses_df = pd.DataFrame(index=range(1, 13))

# Procesar cada año
for year in [año_pasado, año_actual]:
    try:
        # Filtrar por año y contar por mes
        conteo = df[df['ANIO'] == year]['MES'].value_counts().sort_index()
        
        # Unir con el DataFrame completo para asegurar todos los meses
        meses_df = meses_df.join(conteo.rename(year), how='left').fillna(0)
    except Exception as e:
        st.warning(f"Error procesando año {year}: {str(e)}")
        meses_df[year] = 0  # Añadir columna vacía si hay error
    
# Convertir los índices a nombres de mes
# meses_df.index = [nombres_meses[i-1] if 1 <= i <= 12 else f"Mes {int(i)}" for i in meses_df.index]
meses_df.index = nombres_meses

meses_df.index = pd.CategoricalIndex(
    meses_df.index, 
    categories=nombres_meses,
    ordered=True
)
meses_df = meses_df.sort_index()

# Mostrar gráfico con los años seleccionados
st.bar_chart(meses_df[[año_pasado, año_actual]])

# Descargar base de datos
if 'agregar_registros' in st.session_state.get('permisos', []):
    # Preparar archivo CSV para descarga
    csv = df.to_csv(index=False).encode('utf-8')
    
    # Crear botón de descarga
    st.sidebar.subheader("🔧 Herramientas administrativas")
    st.sidebar.download_button(
        label="📥 Descargar base de datos",
        data=csv,
        file_name=f"datos_inscripciones_{hoy.strftime('%Y%m%d')}.csv",
        mime='text/csv',
        help="Descarga completa de todos los registros en formato CSV"
    )

# --- Formulario para nuevos registros (solo para usuarios con permiso) ---
if 'agregar_registros' in st.session_state.get('permisos', []):
    st.subheader("📝 Agregar Nuevo Registro")
    st.info("Complete todos los campos para agregar un nuevo registro")

    # Diccionarios actualizados
    subniveles = {
        "MLK": ["MATERNAL", "PREESCOLAR", "PRIMARIA", "SECUNDARIA"],
        "BACHILLERATO": ["COMPUTACIÓN", "COMUNICACIÓN", "INFORMÁTICA", "MERCADOTECNIA", "PUERICULTURA", "TURISMO"],
        "CEUM": ["ADMINISTRACION", "CRIMINALISTICA", "CONTABILIDAD", "CIENCIAS DE LA EDUCACIÓN", "DERECHO",
                 "GASTRONOMÍA", "INGENIERIA INDUSTRIAL Y DE SISTEMAS", "NEGOCIOS INTERNACIONALES", "ODONTOLOGÍA",
                 "PEDAGOGIA", "PSICOPEDAGOGIA", "SEGURIDAD PÚBLICA", "TSU TURISMO"],
        "ESPECIALIDAD": ["CIRUGÍA BUCAL", "ENDODONCIA", "IMPLANTOLOGIA", "ORTODONCIA", "PERIODONCIA",
                         "REHABILITACION ORAL", "ODONTOLOGIA PEDIATRICA"],
        "MAESTRIA": ["EDUCACIÓN Y DOCENCIA", "JUICIOS ORALES"]
    }

    ciclos = {
        "ESPECIALIDAD": ["AGOSTO DE 25", "FEBRERO DE 25"],
        "CEUM": ["SEPTIEMBRE DE 25", "FEBRERO DE 25"],
        "MAESTRIA": ["SEPTIEMBRE DE 25", "FEBRERO DE 25"],
        "BACHILLERATO": ["SEPTIEMBRE DE 25", "FEBRERO DE 25"],
        "MLK": ["AGOSTO DE 25"]
    }

    nivel = st.selectbox("Nivel académico", list(subniveles.keys()))
    opciones_subnivel = subniveles.get(nivel, [])
    opciones_ciclo = ciclos.get(nivel, [])
    subnivel = st.selectbox("Subnivel / Especialidad", opciones_subnivel)
    ciclo = st.selectbox("Ciclo", opciones_ciclo)

    with st.form("registro_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            fecha = st.date_input("Fecha de inscripción", value=hoy)
            modalidad = st.selectbox("Modalidad", ["MATUTINO", "SABATINO", "ONLINE"])
            nombre = st.text_input("Nombre del estudiante*", placeholder="Requerido")
            grado = st.number_input("Grado", min_value=1, max_value=10, value=1)
            
        with col2:
            telefono = st.text_input("Teléfono*", placeholder="Requerido")
            asesor = st.selectbox("Asesor", ['DAYANA M.', 'MARY H.', 'GUADALUPE T.', 'RICARDO S.','FERNANDA R.','LAURA'])
            medio = st.selectbox("Medio de contacto",
                               ["REDES SOCIALES", "RECOMENDACIÓN", "PÁGINA WEB", "VOLANTE", "OTRO"])
        
        enviar = st.form_submit_button("Guardar registro")
        
        if enviar:
            if not nombre or not telefono:
                st.error("Error: Nombre y Teléfono son campos obligatorios")
            else:
                # Cargar datos actuales desde Google Sheets
                df_actual = st.session_state.df
                
                # Crear nuevo registro - SOLUCIÓN: Usar formato string directamente
                nuevo_id = df_actual["NO"].max() + 1 if not df_actual.empty and 'NO' in df_actual.columns and pd.notna(df_actual["NO"].max()) else 1
                nuevo_registro = {
                    "NO": nuevo_id,
                    "FECHA DE INSCRIPCION": fecha.strftime("%d/%m/%Y"),  # Formato string directamente
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
                df_actualizado = pd.concat([df_actual, nuevo_df], ignore_index=True)
                
                # Guardar en Google Sheets
                if guardar_datos(df_actualizado):
                    st.success("✅ Registro agregado correctamente en Google Sheets!")
                    st.balloons()
                    
                    # Actualizar los datos en session_state
                    st.session_state.df = cargar_datos()
                else:
                    st.error("❌ Error al guardar el registro")
else:
    st.warning("🔒 No tienes permisos para agregar nuevos registros")
    st.info("Contacta al administrador si necesitas acceso")