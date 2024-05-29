import streamlit as st
from google.cloud import documentai_v1 as documentai
from google.oauth2 import service_account
import json
import pandas as pd
import Levenshtein

# Reemplaza esto con tus propios valores
RUTA_CREDENCIALES = '/Users/tom/nuu-test-env-documentai-admin.json'
PROJECT_ID = 'nuu-test-env'
LOCATION = 'us'  # Ejemplo: 'us' o 'eu'
PROCESSOR_ID = '5ff463e1785fadfe'  # Encuentra esto en tu consola de Document AI
datos_unicos = None

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
st.set_page_config(page_title="TOKA - Demo")

with st.sidebar:
    st.image('./img.png')

tab1, tab2, tab3 = st.tabs(["Paso 1 - Captura de Datos", "Paso 2 - Extracción", "Respuesta de Document AI"])

with tab1:
    with st.form("my_form"):
        st.subheader('Datos de Identificación del Contribuyente', divider='blue')
        col1, col2 = st.columns(2)
        with col1:
            rfc = st.text_input("RFC", "")
            denominacion_social = st.text_input("Denominación Social", "")
            regimen_capital = st.text_input("Regimen Capital", "")
            nombre_comercial = st.text_input("Nombre Comercial", "")
        with col2:
            fecha_inicio_operaciones = st.text_input("Fecha Inicio De Operaciones", "")
            status_padron = st.text_input("Estatus en el Padrón", "")
            fecha_ultimo_cambio = st.text_input("Fecha de Ultimo Cambio de Estado", "")

        st.subheader('Datos del Domicilio Registrado', divider='blue')
        col3, col4 = st.columns(2)
        with col3:
            cp = st.text_input("Código Postal", "")
            tipo_vialidad = st.text_input("Tipo Vialidad", "")
            nombre_vialidad = st.text_input("Nombre Vialidad", "")
            numero_exterior = st.text_input("Numero Exterior", "")
            numero_interior = st.text_input("Numero Interior", "")
            nombre_colonia = st.text_input("Nombre Colonia", "")
        with col4:
            nombre_localidad = st.text_input("Nombre Localidad", "")
            nombre_municipio = st.text_input("Nombre Municipio", "")
            entidad_federativa = st.text_input("Entidad Federativa", "")
            entre_calle = st.text_input("Entre Calle", "")
            y_calle = st.text_input("Y Calle", "")

        # Every form must have a submit button.
        submitted = st.form_submit_button("Guardar Datos")

        if submitted:
            st.success("Datos Guardados")

with tab2:
    st.subheader('Carga una Constancia de Situación Fiscal', divider='blue')
    uploaded_file = st.file_uploader("", type=['pdf'],
                                     accept_multiple_files=False)

    if uploaded_file is not None:
        if uploaded_file.size > 5 * 1024 * 1024:  # Mayor a 5 MB
            st.error("El archivo supera el límite de 5MB.")
        else:
            with st.spinner('Procesando...'):
                st.subheader('Comparación de Datos', divider='blue')
                resultado = procesar_documento(uploaded_file)
                datos_unicos = extraer_datos_consolidados_y_unicos(resultado)

                df = pd.DataFrame(
                    [
                        {"Dato": "RFC", "Capturado": rfc, "Extraído": datos_unicos.get("rfc"),
                         "Distancia": Levenshtein.distance(rfc, datos_unicos.get("rfc")),
                         "Similitud": Levenshtein.ratio(rfc, datos_unicos.get("rfc"))},

                        {"Dato": "Denominación Social", "Capturado": denominacion_social, "Extraído":
                            datos_unicos.get("denominacion_social"),
                         "Distancia": Levenshtein.distance(denominacion_social, datos_unicos.get("denominacion_social")),
                         "Similitud": Levenshtein.ratio(denominacion_social, datos_unicos.get("denominacion_social"))},

                        {"Dato": "Regimen Capital", "Capturado": regimen_capital, "Extraído":
                            datos_unicos.get("regimen_capital"),
                         "Distancia": Levenshtein.distance(regimen_capital, datos_unicos.get("regimen_capital")),
                         "Similitud": Levenshtein.ratio(regimen_capital, datos_unicos.get("regimen_capital"))},

                        {"Dato": "Nombre Comercial", "Capturado": nombre_comercial, "Extraído":
                            datos_unicos.get("nombre_comercial"),
                         "Distancia": Levenshtein.distance(nombre_comercial, ""),
                         "Similitud": Levenshtein.ratio(nombre_comercial, datos_unicos.get("nombre_comercial"))},

                        {"Dato": "Fecha Inicio Operaciones", "Capturado": fecha_inicio_operaciones, "Extraído":
                            datos_unicos.get("fecha_inicio_operaciones"),
                         "Distancia": Levenshtein.distance(fecha_inicio_operaciones,
                                                           datos_unicos.get("fecha_inicio_operaciones")),
                         "Similitud": Levenshtein.ratio(fecha_inicio_operaciones,
                                                        datos_unicos.get("fecha_inicio_operaciones"))},

                        {"Dato": "Estatus Padron", "Capturado": status_padron, "Extraído":
                            datos_unicos.get("status_padron"),
                         "Distancia": Levenshtein.distance(status_padron, datos_unicos.get("status_padron")),
                         "Similitud": Levenshtein.ratio(status_padron, datos_unicos.get("status_padron"))},

                        {"Dato": "Fecha Último Cambio", "Capturado": fecha_ultimo_cambio, "Extraído":
                            datos_unicos.get("fecha_ultimo_cambio"),
                         "Distancia": Levenshtein.distance(fecha_ultimo_cambio, datos_unicos.get("fecha_ultimo_cambio")),
                         "Similitud": Levenshtein.ratio(fecha_ultimo_cambio, datos_unicos.get("fecha_ultimo_cambio"))},

                        {"Dato": "Código Postal", "Capturado": cp, "Extraído": datos_unicos.get("cp"),
                         "Distancia": Levenshtein.distance(cp, datos_unicos.get("cp")),
                         "Similitud": Levenshtein.ratio(cp, datos_unicos.get("cp"))},

                        {"Dato": "Tipo Vialidad", "Capturado": tipo_vialidad, "Extraído":
                            datos_unicos.get("tipo_vialidad"),
                         "Distancia": Levenshtein.distance(tipo_vialidad, datos_unicos.get("tipo_vialidad")),
                         "Similitud": Levenshtein.ratio(tipo_vialidad, datos_unicos.get("tipo_vialidad"))},

                        {"Dato": "Nombre Vialidad", "Capturado": nombre_vialidad, "Extraído":
                            datos_unicos.get("nombre_vialidad"),
                         "Distancia": Levenshtein.distance(nombre_vialidad, datos_unicos.get("nombre_vialidad")),
                         "Similitud": Levenshtein.ratio(nombre_vialidad, datos_unicos.get("nombre_vialidad"))},

                        {"Dato": "Número Exterior", "Capturado": numero_exterior, "Extraído":
                            datos_unicos.get("numero_exterior"),
                         "Distancia": Levenshtein.distance(numero_exterior, datos_unicos.get("numero_exterior")),
                         "Similitud": Levenshtein.ratio(numero_exterior, datos_unicos.get("numero_exterior"))},

                        {"Dato": "Número Interior", "Capturado": numero_interior, "Extraído":
                            datos_unicos.get("numero_interior"),
                         "Distancia": Levenshtein.distance(numero_interior, datos_unicos.get("numero_interior")),
                         "Similitud": Levenshtein.ratio(numero_interior, datos_unicos.get("numero_interior"))},

                        {"Dato": "Nombre Colonia", "Capturado": nombre_colonia, "Extraído":
                            datos_unicos.get("nombre_colonia"),
                         "Distancia": Levenshtein.distance(nombre_colonia, datos_unicos.get("nombre_colonia")),
                         "Similitud": Levenshtein.ratio(nombre_colonia, datos_unicos.get("nombre_colonia"))},

                        {"Dato": "Nombre Localidad", "Capturado": nombre_localidad, "Extraído":
                            datos_unicos.get("nombre_localidad"),
                         "Distancia": Levenshtein.distance(nombre_localidad, datos_unicos.get("nombre_localidad")),
                         "Similitud": Levenshtein.ratio(nombre_localidad, datos_unicos.get("nombre_localidad"))},

                        {"Dato": "Nombre Municipio", "Capturado": nombre_municipio, "Extraído":
                            datos_unicos.get("nombre_municipio"),
                         "Distancia": Levenshtein.distance(nombre_municipio, datos_unicos.get("nombre_municipio")),
                         "Similitud": Levenshtein.ratio(nombre_municipio, datos_unicos.get("nombre_municipio"))},

                        {"Dato": "Entidad Federativa", "Capturado": entidad_federativa, "Extraído":
                            datos_unicos.get("entidad_federativa"),
                         "Distancia": Levenshtein.distance(entidad_federativa, datos_unicos.get("entidad_federativa")),
                         "Similitud": Levenshtein.ratio(entidad_federativa, datos_unicos.get("entidad_federativa"))},

                        {"Dato": "Entre Calle", "Capturado": entre_calle, "Extraído":
                            datos_unicos.get("entre_calle"),
                         "Distancia": Levenshtein.distance(entre_calle, datos_unicos.get("entre_calle")),
                         "Similitud": Levenshtein.ratio(entre_calle, datos_unicos.get("entre_calle"))},

                        {"Dato": "Y Calle", "Capturado": y_calle, "Extraído":
                            datos_unicos.get("y_calle"),
                         "Distancia": Levenshtein.distance(y_calle, datos_unicos.get("y_calle")),
                         "Similitud": Levenshtein.ratio(y_calle, datos_unicos.get("y_calle"))},
                    ]
                )
                edited_df = st.data_editor(df)

with tab3:
    json_str = generar_json(datos_unicos)

    # Mostrar el JSON
    st.subheader('Datos Extraídos (JSON)', divider='blue')
    st.text_area("JSON", json_str, height=300)
