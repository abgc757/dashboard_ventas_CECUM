import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Función para cargar datos sin caché
def cargar_datos():
    df = pd.read_csv('datos.csv')
    df["FECHA DE INSCRIPCION"] = pd.to_datetime(df["FECHA DE INSCRIPCION"], dayfirst=True, errors='coerce')
    df['FECHA DE INICIO CICLO ESCOLAR'] = df['FECHA DE INICIO CICLO ESCOLAR'].apply(
        lambda x: convertir_fecha(x) if isinstance(x, str) and " DE " in x.upper() else x
    )
    df["ANIO"] = df["FECHA DE INSCRIPCION"].dt.year
    df["MES"] = df["FECHA DE INSCRIPCION"].dt.month
    return df

# Función para actualizar los datos en la sesión
def actualizar_datos():
    st.session_state.df = cargar_datos()

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
    inscritos_ayer = len(df[df["FECHA DE INSCRIPCION"].dt.date == ayer])
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
    asesor_count = df[df['FECHA DE INSCRIPCION'].dt.year == año_actual]["ASESOR"].value_counts()
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

# Convertir los índices a nombres de mes de forma segura
new_index = []
for i in meses_df.index:
    try:
        if 1 <= i <= 12:
            new_index.append(nombres_meses[i-1])
        else:
            new_index.append(f"Mes {int(i)}")
    except:
        new_index.append(f"Inválido: {i}")

meses_df.index = new_index

# Convertir el índice a categoría ordenada para preservar el orden cronológico
meses_df.index = pd.CategoricalIndex(
    meses_df.index, 
    categories=nombres_meses,
    ordered=True
)

# Ordenar explícitamente por el índice categórico
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
                # Leer el archivo CSV actual directamente
                try:
                    datos_actuales = pd.read_csv('datos.csv')
                except:
                    datos_actuales = pd.DataFrame()
                
                # Crear nuevo registro con formato de fecha modificado
                nuevo_id = datos_actuales["NO"].max() + 1 if not datos_actuales.empty else 1
                nuevo_registro = {
                    "NO": nuevo_id,
                    "FECHA DE INSCRIPCION": fecha.strftime("%d/%m/%Y 00:00"),  # Formato modificado
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

                # Agregar nuevo registro y guardar
                nuevo_df = pd.DataFrame([nuevo_registro])
                datos_actualizados = pd.concat([datos_actuales, nuevo_df], ignore_index=True)
                datos_actualizados.to_csv("datos.csv", index=False)
                
                # Actualizar los datos en session_state
                actualizar_datos()
                
                st.success("✅ Registro agregado correctamente!")
                st.balloons()
else:
    st.warning("🔒 No tienes permisos para agregar nuevos registros")
    st.info("Contacta al administrador si necesitas acceso")