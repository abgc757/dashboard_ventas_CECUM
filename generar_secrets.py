#!/usr/bin/env python3
# # Generar credenciales de para la conexión con Google Sheets

# %%
import json
import os

def convert_json_to_toml(json_path, output_dir=".streamlit"):
    """Convierte un archivo JSON de credenciales de Google a formato TOML para Streamlit"""
    try:
        # Cargar el archivo JSON
        with open(json_path, 'r') as f:
            credentials = json.load(f)
        
        # Crear el directorio de salida si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # Construir el contenido TOML
        toml_content = f"""[gcp_service_account]
type = "{credentials['type']}"
project_id = "{credentials['project_id']}"
private_key_id = "{credentials['private_key_id']}"
private_key = \"""{credentials['private_key']}\"""
client_email = "{credentials['client_email']}"
client_id = "{credentials['client_id']}"
auth_uri = "{credentials['auth_uri']}"
token_uri = "{credentials['token_uri']}"
auth_provider_x509_cert_url = "{credentials['auth_provider_x509_cert_url']}"
client_x509_cert_url = "{credentials['client_x509_cert_url']}"
universe_domain = "{credentials['universe_domain']}"
"""
        # Escribir el archivo TOML
        output_path = os.path.join(output_dir, "secrets.toml")
        with open(output_path, 'w') as f:
            f.write(toml_content)
        
        print(f"Archivo generado con éxito: {output_path}")
        print("IMPORTANTE: Nunca subas este archivo a control de versiones!")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    # Configuración (cambia esto según tus necesidades)
    JSON_FILE_PATH = "accesosDB.json"  # Ruta a tu archivo JSON descargado
    OUTPUT_DIR = ".streamlit"                # Directorio de salida para secrets.toml
    
    convert_json_to_toml(JSON_FILE_PATH, OUTPUT_DIR)
