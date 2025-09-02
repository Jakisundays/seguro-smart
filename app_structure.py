import streamlit as st
import pandas as pd
from io import BytesIO
import base64
from typing import List, Optional
import streamlit as st
from typing import TypedDict, Dict, List, Optional, Union, Literal
import os
import base64
import certifi
import aiohttp
import ssl
from polizas_tools import tools as tools_standard
import asyncio
import fitz  # PyMuPDF
from PIL import Image
import io
from jsonschema import validate, ValidationError
import json
import pandas as pd
from typing import Optional, List, TypedDict, cast
import uuid
import tempfile
import shutil
from dotenv import load_dotenv
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment
import logging
from pathlib import Path


load_dotenv()

# Configurar logger
app_logger = logging.getLogger(__name__)
app_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
app_logger.addHandler(handler)


class QueueItem(TypedDict):
    file_name: str
    file_extension: str
    file_path: str
    media_type: str
    process_id: str
    doc_type: Literal["actual", "renovacion", "adicional"]


# Funciones auxiliares para manejo de archivos
def save_uploaded_file(uploaded_file, doc_type: str) -> Optional[QueueItem]:
    """Guarda un archivo subido directamente en la carpeta downloads y crea un QueueItem"""
    if uploaded_file is None:
        return None

    try:
        # Crear directorio downloads si no existe
        downloads_dir = os.path.join(os.getcwd(), "downloads")
        os.makedirs(downloads_dir, exist_ok=True)

        # Generar nombre único para el archivo
        file_extension = uploaded_file.name.split(".")[-1].lower()
        timestamp = str(int(uuid.uuid4().int))[0:8]
        unique_filename = f"{timestamp}_{uploaded_file.name}"
        file_path = os.path.join(downloads_dir, unique_filename)

        # Guardar el archivo directamente en downloads
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Determinar media type
        media_type_map = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "txt": "text/plain",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
        }

        media_type = media_type_map.get(file_extension, "application/octet-stream")

        # Crear QueueItem
        queue_item: QueueItem = {
            "file_name": uploaded_file.name,
            "file_extension": file_extension,
            "file_path": file_path,
            "media_type": media_type,
            "process_id": str(uuid.uuid4()),
            "doc_type": doc_type,
        }

        return queue_item

    except Exception as e:
        st.error(f"Error al guardar el archivo {uploaded_file.name}: {str(e)}")
        return None


def get_file_info(file_path: str, file_name: str) -> str:
    """Obtiene información del archivo descargado"""
    try:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            return f"✅ **{file_name}** descargado ({file_size_mb:.2f} MB)\n📁 Ubicación: `{file_path}`"
        else:
            return f"❌ Error: No se encontró el archivo {file_name}"
    except Exception as e:
        return f"❌ Error al obtener información de {file_name}: {str(e)}"


def process_files_and_create_queue(
    archivo_actual, archivo_renovacion, archivos_multiples
) -> List[QueueItem]:
    """Procesa todos los archivos y crea la cola de procesamiento"""
    queue_items = []

    # Procesar póliza actual
    if archivo_actual:
        item = save_uploaded_file(archivo_actual, "actual")
        if item:
            queue_items.append(item)

    # Procesar póliza de renovación
    if archivo_renovacion:
        item = save_uploaded_file(archivo_renovacion, "renovacion")
        if item:
            queue_items.append(item)

    # Procesar documentos adicionales
    if archivos_multiples:
        for archivo in archivos_multiples:
            item = save_uploaded_file(archivo, "adicional")
            if item:
                queue_items.append(item)

    return queue_items


class QueueItem(TypedDict):
    file_name: str
    file_extension: str
    file_path: str
    media_type: str
    process_id: str
    doc_type: Literal["actual", "renovacion", "adicional"]


# Configuración de la página
st.set_page_config(
    page_title="SeguroSmart - Análisis de Pólizas",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título principal
st.title("🛡️ SeguroSmart - Sistema de Análisis de Pólizas")
st.markdown("---")

# Área principal - Mostrar estado de la cola si existe
if "queue_items" in st.session_state and st.session_state.queue_items:
    st.header("📊 Estado del Sistema")

    # Métricas generales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de Archivos", len(st.session_state.queue_items))

    with col2:
        actual_count = sum(
            1 for item in st.session_state.queue_items if item["doc_type"] == "actual"
        )
        st.metric("Pólizas Actuales", actual_count)

    with col3:
        renovacion_count = sum(
            1
            for item in st.session_state.queue_items
            if item["doc_type"] == "renovacion"
        )
        st.metric("Pólizas Renovación", renovacion_count)

    with col4:
        adicional_count = sum(
            1
            for item in st.session_state.queue_items
            if item["doc_type"] == "adicional"
        )
        st.metric("Documentos Adicionales", adicional_count)

    st.markdown("---")

    # Tabla detallada de la cola
    st.subheader("📋 Cola de Procesamiento Actual")

    queue_display_data = []
    for i, item in enumerate(st.session_state.queue_items, 1):
        queue_display_data.append(
            {
                "#": i,
                "Archivo": item["file_name"],
                "Tipo de Documento": item["doc_type"].title(),
                "Extensión": item["file_extension"].upper(),
                "Media Type": item["media_type"],
                "Process ID": item["process_id"],
                "Estado": "🟢 En Cola",
            }
        )

    df_detailed = pd.DataFrame(queue_display_data)
    st.dataframe(df_detailed, use_container_width=True)

    # Botón para limpiar la cola
    if st.button("🗑️ Limpiar Cola", type="secondary"):
        # Limpiar archivos descargados
        deleted_count = 0
        for item in st.session_state.queue_items:
            try:
                if os.path.exists(item["file_path"]):
                    os.remove(item["file_path"])
                    deleted_count += 1
            except Exception as e:
                st.warning(f"No se pudo eliminar el archivo {item['file_name']}: {e}")

        # Limpiar session state
        st.session_state.queue_items = []
        st.success(
            f"✅ Cola limpiada exitosamente. Se eliminaron {deleted_count} archivo(s) de la carpeta downloads."
        )
        st.rerun()

    st.markdown("---")
else:
    st.info(
        "👈 Utiliza la barra lateral para cargar archivos y comenzar el procesamiento."
    )
    st.markdown("---")


class InvoiceOrchestrator:
    def __init__(
        self,
        api_key: str,
        model: str,
    ):
        self.api_key = api_key
        self.model = model

    # Hace requests a la API con reintentos
    async def make_api_request(
        self, url: str, headers: Dict, data: Dict, process_id: str, retries: int = 5
    ) -> Optional[Dict]:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            for i in range(retries):
                try:
                    async with session.post(
                        url, headers=headers, json=data
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status in [429, 529, 503]:
                            sleep_time = 15 * (i + 1)  # Espera incremental en segundos
                            app_logger.warning(
                                f"API request failed with status {response.status}. Retrying in {sleep_time} seconds..."
                            )
                            await asyncio.sleep(sleep_time)
                        else:
                            app_logger.error(
                                f"API request failed with status {response.status} - {await response.text()}"
                            )
                            raise ValueError(
                                f"Request failed with status {response.status}"
                            )
                except aiohttp.ClientError as e:
                    raise ValueError(f"Request error: {str(e)}")
        raise ValueError("Max retries exceeded.")

    async def handle_pdf(self, item: QueueItem):
        file_path = Path(item["file_path"])
        encoded_pdf = base64.b64encode(file_path.read_bytes()).decode()

        prompt = (
            tools_standard[1]["prompt"]
            if item["doc_type"] == "adicional"
            else tools_standard[0]["prompt"]
        )
        responseSchema = (
            tools_standard[1]["data"]
            if item["doc_type"] == "adicional"
            else tools_standard[0]["data"]
        )
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "application/pdf",
                                "data": encoded_pdf,
                            }
                        },
                        {"text": prompt},
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": responseSchema,
            },
        }
        response = await self.make_api_request(
            url, headers, payload, item["process_id"]
        )
        item["data"] = response
        return item


orchestrator = InvoiceOrchestrator(
    api_key=os.getenv("GEMINI_API_KEY"),
    model="gemini-2.5-flash",
)


# Barra lateral
with st.sidebar:

    # Campo 1: Póliza Actual
    st.subheader("1️⃣ Póliza Actual")
    archivo_poliza_actual = st.file_uploader(
        "Cargar archivo de póliza actual",
        type=["pdf", "docx", "txt", "jpg", "png"],
        key="poliza_actual",
        help="Sube el archivo de tu póliza actual para extraer sus datos",
    )

    st.markdown("---")

    # Campo 2: Póliza de Renovación
    st.subheader("2️⃣ Póliza de Renovación")
    archivo_poliza_renovacion = st.file_uploader(
        "Cargar archivo de póliza de renovación",
        type=["pdf", "docx", "txt", "jpg", "png"],
        key="poliza_renovacion",
        help="Sube el archivo de la póliza de renovación para comparar",
    )

    st.markdown("---")

    # Campo 3: Múltiples Documentos
    st.subheader("3️⃣ Documentos Adicionales")
    archivos_multiples = st.file_uploader(
        "Cargar múltiples documentos",
        type=["pdf", "docx", "txt", "jpg", "png"],
        accept_multiple_files=True,
        key="documentos_multiples",
        help="Sube múltiples documentos para extraer las primas de cada uno",
    )

    st.markdown("---")

    # Botón de procesamiento
if st.sidebar.button(
    "🚀 Iniciar Proceso",
    type="primary",
    use_container_width=True,
    help="Haz clic para iniciar el procesamiento de todos los archivos cargados",
):
    # Verificar que al menos un archivo esté cargado
    if (
        not archivo_poliza_actual
        and not archivo_poliza_renovacion
        and not archivos_multiples
    ):
        st.error("⚠️ Por favor, carga al menos un archivo antes de iniciar el proceso.")
    else:
        # Crear contenedor para mostrar el progreso
        with st.spinner("Procesando archivos..."):
            # Procesar archivos y crear cola
            queue_items = process_files_and_create_queue(
                archivo_poliza_actual, archivo_poliza_renovacion, archivos_multiples
            )

            # st.write(queue_items)

            if queue_items:
                st.success(
                    f"✅ Se procesaron {len(queue_items)} archivo(s) exitosamente."
                )

                # Mostrar información de la cola
                st.subheader("📋 Cola de Procesamiento")

                # Crear DataFrame para mostrar la información
                queue_data = []
                for item in queue_items:
                    queue_data.append(
                        {
                            "Archivo": item["file_name"],
                            "Tipo": item["doc_type"].title(),
                            "Extensión": item["file_extension"].upper(),
                            "Process ID": item["process_id"][:8] + "...",
                            "Estado": "✅ Listo para procesar",
                        }
                    )

                df_queue = pd.DataFrame(queue_data)
                st.dataframe(df_queue, use_container_width=True)

                # Sección de archivos descargados
                st.subheader("📁 Archivos Descargados")

                for item in queue_items:
                    if item["media_type"] == "application/pdf":
                        result = asyncio.run(orchestrator.handle_pdf(item))

                        # result = asyncio.run(orchestrator.run_pdf_toolchain(item))

                        st.write(result)

            else:
                st.error(
                    "❌ No se pudieron procesar los archivos. Verifica que los archivos sean válidos."
                )
