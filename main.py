import streamlit as st
from google.cloud import documentai_v1 as documentai
from google.oauth2 import service_account
import json

# Reemplaza esto con tus propios valores
RUTA_CREDENCIALES = '/Users/tom/nuu-test-env-documentai-admin.json'
PROJECT_ID = 'nuu-test-env'
LOCATION = 'us'  # Ejemplo: 'us' o 'eu'
PROCESSOR_ID = '5ff463e1785fadfe'  # Encuentra esto en tu consola de Document AI

# Autenticación con Google Cloud
# Obtén las credenciales de la variable de entorno

# credenciales_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
# credenciales_dict = json.loads(credenciales_json)
# credentials = service_account.Credentials.from_service_account_info(credenciales_dict)

credentials = service_account.Credentials.from_service_account_file(RUTA_CREDENCIALES)
client = documentai.DocumentProcessorServiceClient(credentials=credentials)


def procesar_documento(file):
    nombre_procesador = client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
    documento = {"content": file.getvalue(), "mime_type": "application/pdf"}

    request = documentai.ProcessRequest(name=nombre_procesador, raw_document=documento)
    result = client.process_document(request=request)

    return result


def extraer_datos_consolidados_y_unicos(result):
    # Estructura para consolidar los datos de manera única: {'campo': valor o [valores], ...}
    datos_unicos = {}

    for entity in result.document.entities:
        field_name = entity.type_
        field_value = entity.mention_text

        # Manejar entidades con propiedades anidadas (como filas con valores)
        if entity.properties:
            sub_fields = {}
            for property in entity.properties:
                sub_field_name = property.type_
                sub_field_value = property.mention_text
                # Para campos anidados, solo se agrega si la clave principal no existía previamente
                if sub_field_name not in sub_fields:
                    sub_fields[sub_field_name] = sub_field_value

            # Si el campo ya existe, se ignora esta instancia
            if field_name not in datos_unicos:
                datos_unicos[field_name] = [sub_fields] if sub_fields else field_value
        else:
            # Para campos simples, se agrega el valor si la clave no existía previamente
            if field_name not in datos_unicos:
                datos_unicos[field_name] = field_value

    return datos_unicos


def generar_json(datos_unicos):
    # Convertir los datos únicos consolidados a JSON
    json_str = json.dumps(datos_unicos, ensure_ascii=False, indent=4)
    return json_str

# Configuración inicial de Streamlit


st.set_page_config(page_title="BIRMEX - Demo")
st.image('./img.png')

uploaded_file = st.file_uploader("Carga una Constancia de Situación Fiscal", type=['pdf'], accept_multiple_files=False)

if uploaded_file is not None:
    if uploaded_file.size > 5 * 1024 * 1024:  # Mayor a 5 MB
        st.error("El archivo supera el límite de 5MB.")
    else:
        with st.spinner('Procesando...'):
            resultado = procesar_documento(uploaded_file)
            datos_unicos = extraer_datos_consolidados_y_unicos(resultado)

            #json_str = generar_json(datos_unicos)

            # Mostrar el JSON
            # st.subheader("Datos Extraídos (JSON):")
            # st.text_area("JSON", json_str, height=300)