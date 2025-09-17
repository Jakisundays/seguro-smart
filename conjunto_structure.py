import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io
import base64
import requests
import json
from polizas_tools2 import tools as tools_standard
from dotenv import load_dotenv

load_dotenv()

# Configuración de la página
st.set_page_config(
    page_title="SeguroSmart - Carga de Archivos",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com"


def main():
    # Título principal
    st.title("SeguroSmart - Gestor de Archivos")

    # Barra lateral
    with st.sidebar:
        st.header("Convertidor PDF a Base64")

        # Widget de carga múltiple de archivos
        uploaded_files = st.file_uploader(
            "Selecciona archivos PDF:",
            accept_multiple_files=True,
            type=["pdf"],
            help="Selecciona uno o más archivos PDF para convertir a Base64",
        )

        # Botón para convertir PDFs a base64
        convert_pdfs = st.button("Convertir a Base64", use_container_width=True)

        # Botón para limpiar archivos cargados
        if st.button("Limpiar", use_container_width=True):
            st.rerun()

    # Contenido principal
    if convert_pdfs and uploaded_files:
        pdf_files = [f for f in uploaded_files if f.type == "application/pdf"]
        if pdf_files:
            st.header("PDFs Convertidos a Base64")

            base64_docs = []

            for pdf_file in pdf_files:
                st.subheader(f"{pdf_file.name}")

                # Convertir PDF a base64
                pdf_bytes = pdf_file.getvalue()
                pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
                base64_docs.append(pdf_base64)

            files_metadata_b64 = [
                {"inline_data": {"mime_type": "application/pdf", "data": doc}}
                for doc in base64_docs
            ]

            prompt = tools_standard[1]["prompt"]
            responseSchema = tools_standard[1]["data"]

            payload = {
                "contents": [{"parts": files_metadata_b64 + [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": responseSchema,
                },
            }

            response = requests.post(
                f"{BASE_URL}/v1beta/models/gemini-2.5-flash:generateContent?key={GOOGLE_API_KEY}",
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
            )

            if response.status_code == 200:
                st.success("Respuesta de la API:")
                st.json(response.json())
            else:
                st.error(
                    f"Error en la solicitud: {response.status_code} - {response.text}"
                )

        else:
            st.warning("No se encontraron archivos PDF para convertir.")
    elif uploaded_files and not convert_pdfs:
        st.info("Archivos PDF cargados. Presiona 'Convertir a Base64' para procesar.")
    else:
        st.info("Selecciona archivos PDF en la barra lateral para comenzar.")


if __name__ == "__main__":
    main()
