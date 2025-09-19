import streamlit as st
import pandas as pd
from io import BytesIO
import base64
from typing import List, Optional
from typing import TypedDict, Dict, List, Optional, Literal
import os
import certifi
import aiohttp
import ssl
from polizas_tools import tools as tools_standard
import asyncio
from typing import Optional, List, TypedDict
import uuid
from dotenv import load_dotenv
import logging
from pathlib import Path
from dataclasses import dataclass, field
import json
from openpyxl.styles import Font, Alignment


@dataclass
class Prima:
    """
    Representa el valor de una prima individual con desglose de IVA.
    """

    prima_sin_iva: float
    iva: float
    prima_con_iva: float


@dataclass
class DetalleCoberturaItem:
    """
    Representa un interés asegurado con su valor asegurado.
    """

    interes_asegurado: str  # Ejemplo: "Edificio", "Maquinaria"
    valor_asegurado: float  # Valor monetario asegurado


@dataclass
class Cobertura:
    """
    Representa el detalle completo de la cobertura.
    """

    detalle_cobertura: List[DetalleCoberturaItem] = field(default_factory=list)
    total_valores_asegurados: float = 0.0

    def calcular_total(self) -> float:
        """
        Calcula y actualiza la suma total de los valores asegurados.
        """
        self.total_valores_asegurados = sum(
            item.valor_asegurado for item in self.detalle_cobertura
        )
        return self.total_valores_asegurados


@dataclass
class QueueItem(TypedDict):
    file_name: str
    file_extension: str
    file_path: str
    media_type: str
    process_id: str
    doc_type: Literal["actual", "renovacion", "adicional", "conjunto"]


load_dotenv()

# Configurar logger
app_logger = logging.getLogger(__name__)
app_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
app_logger.addHandler(handler)


def cleanup_processed_files(queue_items_list):
    """Elimina automáticamente los archivos después del procesamiento exitoso"""
    deleted_files = []
    failed_deletions = []

    for item in queue_items_list:
        try:
            if os.path.exists(item["file_path"]):
                os.remove(item["file_path"])
                deleted_files.append(item["file_name"])
                app_logger.info(
                    f"Archivo eliminado automáticamente: {item['file_name']}"
                )
        except Exception as e:
            failed_deletions.append((item["file_name"], str(e)))
            app_logger.error(f"Error al eliminar archivo {item['file_name']}: {str(e)}")

    return deleted_files, failed_deletions


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
    archivo_actual, archivo_renovacion, archivos_multiples, conjunto_documentos
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

    if conjunto_documentos:
        for doc in conjunto_documentos:
            pdf_bytes = doc.read()
            base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
            document = {
                "file_name": doc.name,
                "file_extension": doc.name.split(".")[-1].lower(),
                "media_type": "application/pdf",
                "process_id": str(uuid.uuid4()),
                "doc_type": "conjunto",
                "base64": base64_pdf,
            }
            queue_items.append(document)

    return queue_items


def separar_archivos_por_tipo(archivos):
    conjuntos = []
    otros = []

    for archivo in archivos:
        if archivo.get("doc_type") == "conjunto":
            conjuntos.append(archivo)
        else:
            otros.append(archivo)

    return conjuntos, otros


def listar_valores_asegurados(poliza_json, tipo_documento):
    with st.expander("Detalles de la Póliza"):
        st.write(poliza_json)
    archivo = poliza_json.get("file_name", "Desconocido")
    total_poliza = poliza_json.get("total_valores_asegurados", 0)

    resultado = []
    for item in poliza_json.get("detalle_cobertura", []):
        resultado.append(
            {
                "Archivo": archivo,
                "Tipo de Documento": tipo_documento,
                "Interés Asegurado": item.get("interes_asegurado"),
                "Valor Asegurado": item.get("valor_asegurado"),
                "Total Póliza": total_poliza,
            }
        )

    return resultado


# def x():


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

    async def batch_processor(self, input_files):
        if not input_files:
            return

        base64_docs = []

        for file in input_files:
            base64_docs.append(file["base64"])

        # # Construir payload
        files_metadata_b64 = [
            {"inline_data": {"mime_type": "application/pdf", "data": doc}}
            for doc in base64_docs
        ]

        prompt = tools_standard[1]["prompt"]
        responseSchema = tools_standard[1]["data"]

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={orchestrator.api_key}"

        headers = {"Content-Type": "application/json"}

        payload = {
            "contents": [{"parts": files_metadata_b64 + [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": responseSchema,
            },
        }

        response = await self.make_api_request(
            url=url, headers=headers, data=payload, process_id="Dinardi"
        )

        response["doc_type"] = input_files[0]["doc_type"]

        return response


orchestrator = InvoiceOrchestrator(
    api_key=os.getenv("GEMINI_API_KEY"),
    model="gemini-2.5-flash",
)

# Configuración de la página
st.set_page_config(
    page_title="Análisis de pólizas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


async def main():
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

        # campo 4: Conjunto de documentos
        st.subheader("4️⃣ Conjunto de Documentos adicionales")
        archivos_conjuntos = st.file_uploader(
            "Cargar conjunto de documentos",
            type=["pdf", "docx", "txt", "jpg", "png"],
            accept_multiple_files=True,
            key="archivos_conjuntos",
            help="Sube un conjunto de documentos para extraer información de todos ellos",
        )

        st.markdown("---")

    if st.sidebar.button(
        "🚀 Iniciar Proceso",
        type="primary",
        use_container_width=True,
        help="Haz clic para iniciar el procesamiento de todos los archivos cargados",
    ):
        if (
            archivo_poliza_actual
            or archivo_poliza_renovacion
            or archivos_multiples
            or archivos_conjuntos
        ):

            queue_items = process_files_and_create_queue(
                archivo_poliza_actual,
                archivo_poliza_renovacion,
                archivos_multiples,
                archivos_conjuntos,
            )

            conjuntos, otros = separar_archivos_por_tipo(queue_items)

            tasks = []

            if otros:
                for item in otros:
                    tasks.append(orchestrator.handle_pdf(item))

            if conjuntos:
                procesos_conjuntos = orchestrator.batch_processor(conjuntos)
                tasks.append(procesos_conjuntos)

            with st.spinner("Procesando..."):
                results = await asyncio.gather(*tasks)

            with st.expander("Resultados"):
                st.write(results)

            poliza_actual = None
            poliza_renovacion = None
            docs_adicionales = []
            doc_conjuntos = None

            with st.expander("Actual"):
                for item in results:
                    if item.get("doc_type") == "actual":
                        poliza_actual = json.loads(
                            item.get("data")
                            .get("candidates")[0]
                            .get("content", {})
                            .get("parts", [{}])[0]
                            .get("text", "")
                        )
                        poliza_actual["file_name"] = item.get("file_name")
                        st.write(poliza_actual)

            with st.expander("Renovación"):
                for item in results:
                    if item.get("doc_type") == "renovacion":
                        poliza_renovacion = json.loads(
                            item.get("data")
                            .get("candidates")[0]
                            .get("content", {})
                            .get("parts", [{}])[0]
                            .get("text", "")
                        )
                        poliza_renovacion["file_name"] = item.get("file_name")
                        st.write(poliza_renovacion)

            with st.expander("Adicional"):
                for item in results:
                    if item.get("doc_type") == "adicional":
                        doc_adicional = json.loads(
                            item.get("data")
                            .get("candidates")[0]
                            .get("content", {})
                            .get("parts", [{}])[0]
                            .get("text", "")
                        )
                        doc_adicional["file_name"] = item.get("file_name")
                        docs_adicionales.append(doc_adicional)
                        st.write(doc_adicional)

            with st.expander("Conjunto"):
                for item in results:
                    if item.get("doc_type") == "conjunto":
                        doc_conjuntos = json.loads(
                            item.get("candidates")[0]
                            .get("content", {})
                            .get("parts", [{}])[0]
                            .get("text", "")
                        )
                        doc_conjuntos["file_name"] = item.get("file_name")
                        st.write(doc_conjuntos)

            if poliza_actual:
                poliza_data_actual = listar_valores_asegurados(poliza_actual, "Actual")
            else:
                poliza_data_actual = []
            if poliza_renovacion:
                poliza_data_renovacion = listar_valores_asegurados(
                    poliza_renovacion, "Renovacion"
                )
            else:
                poliza_data_renovacion = []
            if docs_adicionales:
                docs_adicionales_data = [
                    {
                        "Archivo": doc.get("file_name"),
                        "Tipo de Documento": "Adicional",
                        "Prima Sin IVA": doc.get("prima_sin_iva", 0),
                        "IVA": doc.get("iva", 0),
                        "Prima Con IVA": doc.get("prima_con_iva", 0),
                    }
                    for doc in docs_adicionales
                ]
            else:
                docs_adicionales_data = []

            with st.expander("Poliza Data Actual"):
                st.write(poliza_data_actual)

            with st.expander("Poliza Data Renovacion"):
                st.write(poliza_data_renovacion)

            with st.expander("Docs Adicionales"):
                st.write(docs_adicionales_data)

            df_polizas = pd.DataFrame(poliza_data_actual + poliza_data_renovacion)

            polizas_actuales = df_polizas[df_polizas["Tipo de Documento"] == "Actual"]
            polizas_renovacion = df_polizas[
                df_polizas["Tipo de Documento"] == "Renovacion"
            ]

            if not polizas_actuales.empty:
                poliza_actual_cuadro = [
                    {
                        "Interés Asegurado": poliza["Interés Asegurado"],
                        "Valor Asegurado": poliza["Valor Asegurado"],
                    }
                    for poliza in poliza_data_actual
                ]
                st.subheader("📋 Pólizas Actuales")
                df_actuales_display = polizas_actuales.copy()
                df_actuales_display["Valor Asegurado"] = df_actuales_display[
                    "Valor Asegurado"
                ].apply(lambda x: f"${x:,.0f}")
                df_actuales_display["Total Póliza"] = df_actuales_display[
                    "Total Póliza"
                ].apply(lambda x: f"${x:,.0f}")
                st.dataframe(poliza_actual_cuadro, use_container_width=True)

                st.markdown("---")

            if not polizas_renovacion.empty:
                poliza_renovacion_cuadro = [
                    {
                        "Interés Asegurado": poliza["Interés Asegurado"],
                        "Valor Asegurado": poliza["Valor Asegurado"],
                    }
                    for poliza in poliza_data_renovacion
                ]
                st.subheader("🔄 Pólizas de Renovación")
                df_renovacion_display = polizas_renovacion.copy()
                df_renovacion_display["Valor Asegurado"] = df_renovacion_display[
                    "Valor Asegurado"
                ].apply(lambda x: f"${x:,.0f}")
                df_renovacion_display["Total Póliza"] = df_renovacion_display[
                    "Total Póliza"
                ].apply(lambda x: f"${x:,.0f}")
                st.dataframe(poliza_renovacion_cuadro, use_container_width=True)

                # Métrica del total
                total_renovacion = (
                    polizas_renovacion["Total Póliza"].iloc[0]
                    if len(polizas_renovacion) > 0
                    else 0
                )
                st.metric(
                    "💰 Total Póliza Renovación",
                    f"${total_renovacion:,.0f}",
                )

                st.markdown("---")

            if docs_adicionales:
                solo_primas = [
                    {
                        "Archivo": item["Archivo"],
                        "Prima Sin IVA": item["Prima Sin IVA"],
                        "IVA": item["IVA"],
                        "Prima Con IVA": item["Prima Con IVA"],
                    }
                    for item in docs_adicionales_data
                ]
                df_primas = pd.DataFrame(solo_primas)

                # Formatear valores monetarios para visualización
                df_primas_display = df_primas.copy()
                df_primas_display["Prima Sin IVA"] = df_primas_display[
                    "Prima Sin IVA"
                ].apply(lambda x: f"${x:,.0f}")
                df_primas_display["IVA"] = df_primas_display["IVA"].apply(
                    lambda x: f"${x:,.0f}"
                )
                df_primas_display["Prima Con IVA"] = df_primas_display[
                    "Prima Con IVA"
                ].apply(lambda x: f"${x:,.0f}")

                st.dataframe(solo_primas, use_container_width=True)

                st.markdown("---")

            if poliza_data_actual or docs_adicionales_data:
                st.subheader("📥 Descargar Resultados")

                # Crear archivo Excel en memoria con datos filtrados y formato profesional
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    from openpyxl.styles import (
                        Font,
                        PatternFill,
                        Border,
                        Side,
                        Alignment,
                    )
                    from openpyxl.utils import get_column_letter

                    # Definir estilos
                    header_font = Font(
                        name="Calibri", size=12, bold=True, color="FFFFFF"
                    )
                    header_fill = PatternFill(
                        start_color="2E75B6",
                        end_color="2E75B6",
                        fill_type="solid",
                    )
                    data_font = Font(name="Calibri", size=11)
                    border = Border(
                        left=Side(style="thin", color="D0D0D0"),
                        right=Side(style="thin", color="D0D0D0"),
                        top=Side(style="thin", color="D0D0D0"),
                        bottom=Side(style="thin", color="D0D0D0"),
                    )
                    center_alignment = Alignment(horizontal="center", vertical="center")
                    currency_alignment = Alignment(
                        horizontal="right", vertical="center"
                    )
                    left_alignment = Alignment(horizontal="left", vertical="center")

                    def format_worksheet(ws, df, sheet_type):
                        # Insertar fila para el título
                        ws.insert_rows(1, 2)  # Insertar 2 filas al inicio

                        # Agregar título en la primera fila
                        title_cell = ws.cell(row=1, column=1)
                        title_cell.value = "CENTRO DE DIAGNOSTICO AUTOMOTOR DE PALMIRA"

                        title_font = Font(
                            name="Arial", size=16, bold=True, color="FFFFFF"
                        )
                        title_fill = PatternFill(
                            start_color="1F4E79",
                            end_color="1F4E79",
                            fill_type="solid",
                        )
                        title_alignment = Alignment(
                            horizontal="center", vertical="center"
                        )

                        title_cell.font = title_font
                        title_cell.fill = title_fill
                        title_cell.alignment = title_alignment

                        # Combinar celdas para el título (toda la fila)
                        ws.merge_cells(
                            start_row=1,
                            start_column=1,
                            end_row=1,
                            end_column=len(df.columns),
                        )

                        # Formato especial para etiquetas de pólizas consolidadas
                        if sheet_type == "polizas":
                            label_font = Font(
                                name="Arial", size=14, bold=True, color="FFFFFF"
                            )
                            label_fill = PatternFill(
                                start_color="4472C4",
                                end_color="4472C4",
                                fill_type="solid",
                            )

                            # Buscar y formatear etiquetas de pólizas
                            for row_num in range(3, ws.max_row + 1):
                                cell_value = ws.cell(row=row_num, column=1).value
                                if cell_value and (
                                    "PÓLIZAS ACTUALES" in str(cell_value)
                                    or "PÓLIZAS DE RENOVACIÓN" in str(cell_value)
                                ):
                                    # Aplicar formato a la etiqueta
                                    label_cell = ws.cell(row=row_num, column=1)
                                    label_cell.font = label_font
                                    label_cell.fill = label_fill
                                    label_cell.alignment = title_alignment

                                    # Combinar celdas para la etiqueta
                                    ws.merge_cells(
                                        start_row=row_num,
                                        start_column=1,
                                        end_row=row_num,
                                        end_column=len(df.columns),
                                    )

                        # Aplicar formato a encabezados (ahora en la fila 3)
                        for col_num in range(1, len(df.columns) + 1):
                            cell = ws.cell(row=3, column=col_num)
                            cell.font = header_font
                            cell.fill = header_fill
                            cell.border = border
                            cell.alignment = center_alignment

                        # Aplicar formato a datos (ahora empezando desde la fila 4)
                        for row_num in range(4, len(df) + 4):
                            for col_num in range(1, len(df.columns) + 1):
                                cell = ws.cell(row=row_num, column=col_num)
                                cell.font = data_font
                                cell.border = border

                                # Aplicar alineación según el tipo de columna
                                col_name = df.columns[col_num - 1]
                                if (
                                    "valor" in col_name.lower()
                                    or "prima" in col_name.lower()
                                    or "iva" in col_name.lower()
                                ):
                                    cell.alignment = currency_alignment
                                    # Formatear como moneda
                                    if isinstance(cell.value, (int, float)):
                                        cell.number_format = "$#,##0"
                                elif col_name.lower() == "coberturas":
                                    cell.alignment = left_alignment
                                else:
                                    cell.alignment = center_alignment

                        # Ajustar ancho de columnas
                        for col_num in range(1, len(df.columns) + 1):
                            column_letter = get_column_letter(col_num)
                            col_name = df.columns[col_num - 1]

                            # Calcular ancho basado en el contenido (incluyendo el título)
                            max_length = max(
                                len(str(col_name)),
                                len("CENTRO DE DIAGNOSTICO AUTOMOTOR DE PALMIRA")
                                // len(df.columns),
                            )
                            for row_num in range(4, len(df) + 4):
                                cell_value = str(
                                    ws.cell(row=row_num, column=col_num).value or ""
                                )
                                max_length = max(max_length, len(cell_value))

                            # Establecer ancho específico para la columna Coberturas
                            if col_name.lower() == "coberturas":
                                width = 45  # Ancho específico para coberturas
                            else:
                                # Establecer ancho mínimo y máximo para otras columnas
                                width = min(max(max_length + 2, 15), 30)

                            ws.column_dimensions[column_letter].width = width

                        # Aplicar filtros automáticos
                        ws.auto_filter.ref = (
                            f"A1:{get_column_letter(len(df.columns))}{len(df) + 1}"
                        )

                        # Congelar primera fila
                        ws.freeze_panes = "A2"

                    # Crear primero la hoja "Análisis_Estructurado" para que sea la primera pestaña
                    if poliza_actual_cuadro and poliza_renovacion_cuadro and docs_adicionales_data:
                        # Crear estructura organizada con 4 columnas específicas

                        # Obtener datos únicos de intereses asegurados
                        intereses_unicos = list(
                            set(
                                [item["interes_asegurado"] for item in poliza_actual_cuadro]
                                + [
                                    item["interes_asegurado"]
                                    for item in poliza_renovacion_cuadro
                                ]
                            )
                        )

                        # Crear diccionarios para búsqueda rápida
                        valores_actuales = {
                            item["interes_asegurado"]: item["valor_asegurado"]
                            for item in poliza_actual_cuadro
                        }
                        valores_renovacion = {
                            item["interes_asegurado"]: item["valor_asegurado"]
                            for item in poliza_renovacion_cuadro
                        }

                        # Calcular totales
                        total_actual = sum(valores_actuales.values())
                        total_renovacion = sum(valores_renovacion.values())

                        # Crear datos estructurados
                        datos_estructurados = []

                        # Agregar filas de intereses asegurados
                        for interes in sorted(intereses_unicos):
                            datos_estructurados.append(
                                {
                                    "Interés Asegurado": interes,
                                    "Valor Asegurado Actual": valores_actuales.get(
                                        interes, 0
                                    ),
                                    "Valor Asegurado Renovado": valores_renovacion.get(
                                        interes, 0
                                    ),
                                    "Primas": "",
                                }
                            )

                        # Agregar fila de totales
                        datos_estructurados.append(
                            {
                                "Interés Asegurado": "TOTAL",
                                "Valor Asegurado Actual": total_actual,
                                "Valor Asegurado Renovado": total_renovacion,
                                "Primas": "",
                            }
                        )

                        # Crear estructura base con columnas dinámicas para primas
                        # Definir lista de coberturas
                        coberturas = [
                            "Incendio y/o Rayo Edificios",
                            "Explosión Mejoras Locativas",
                            "Terremoto, temblor Muebles y Enseres",
                            "Asonada, motin, conm. Civil/popular huelga Mercancias Fijas",
                            "Extension de amparo",
                            "Daños por agua, Anegación Dineros",
                            "Incendio y/o Rayo en aparatos electricos Equipo Electronico",
                        ]

                        columnas_base = [
                            "Coberturas",
                            "Interés Asegurado",
                            "Valor Asegurado Actual",
                            "Valor Asegurado Renovado",
                        ]

                        # Agregar columnas para cada archivo de prima
                        columnas_primas = []
                        if solo_primas:
                            for prima in solo_primas:
                                nombre_archivo = prima["Archivo"]
                                if nombre_archivo not in columnas_primas:
                                    columnas_primas.append(nombre_archivo)

                        # Crear todas las columnas
                        todas_columnas = columnas_base + columnas_primas

                        # Inicializar datos estructurados con todas las columnas
                        datos_estructurados = []

                        # Crear mapas de valores de prima por archivo
                        valores_prima_por_archivo = {}
                        if solo_primas:
                            for prima in solo_primas:
                                nombre_archivo = prima["Archivo"]
                                valores_prima_por_archivo[nombre_archivo] = [
                                    f"${prima['Prima Sin IVA']:,.0f}",
                                ]

                        # Determinar el número máximo de filas necesarias
                        intereses_ordenados = sorted(intereses_unicos)
                        max_filas = max(len(intereses_ordenados), len(coberturas))

                        # Agregar filas con coberturas e intereses asegurados
                        for i in range(max_filas):
                            fila = {
                                "Coberturas": (
                                    coberturas[i] if i < len(coberturas) else ""
                                ),
                                "Interés Asegurado": (
                                    intereses_ordenados[i]
                                    if i < len(intereses_ordenados)
                                    else ""
                                ),
                                "Valor Asegurado Actual": (
                                    valores_actuales.get(intereses_ordenados[i], 0)
                                    if i < len(intereses_ordenados)
                                    else ""
                                ),
                                "Valor Asegurado Renovado": (
                                    valores_renovacion.get(intereses_ordenados[i], 0)
                                    if i < len(intereses_ordenados)
                                    else ""
                                ),
                            }

                            # Agregar valores de prima en las primeras filas
                            for col_prima in columnas_primas:
                                if col_prima in valores_prima_por_archivo and i < 1:
                                    fila[col_prima] = valores_prima_por_archivo[
                                        col_prima
                                    ][i]
                                else:
                                    fila[col_prima] = ""

                            datos_estructurados.append(fila)

                        # Agregar fila de totales
                        fila_total = {
                            "Coberturas": "",
                            "Interés Asegurado": "TOTAL",
                            "Valor Asegurado Actual": total_actual,
                            "Valor Asegurado Renovado": total_renovacion,
                        }
                        # Inicializar columnas de primas vacías para totales
                        for col_prima in columnas_primas:
                            fila_total[col_prima] = ""
                        datos_estructurados.append(fila_total)

                        # Crear DataFrame estructurado con columnas ordenadas
                        df_estructurado = pd.DataFrame(
                            datos_estructurados, columns=todas_columnas
                        )

                        # Validación de integridad de datos
                        if (
                            abs(
                                total_actual
                                - sum(
                                    item["valor_asegurado"] for item in poliza_actual_cuadro
                                )
                            )
                            > 0.01
                        ):
                            st.warning(
                                "⚠️ Advertencia: Discrepancia detectada en totales actuales"
                            )

                        if (
                            abs(
                                total_renovacion
                                - sum(
                                    item["valor_asegurado"] for item in poliza_renovacion_cuadro
                                )
                            )
                            > 0.01
                        ):
                            st.warning(
                                "⚠️ Advertencia: Discrepancia detectada en totales de renovación"
                            )

                        # Exportar a Excel
                        df_estructurado.to_excel(
                            writer,
                            sheet_name="Análisis_Estructurado",
                            index=False,
                        )
                        format_worksheet(
                            writer.sheets["Análisis_Estructurado"],
                            df_estructurado,
                            "polizas",
                        )

                    # Crear las otras hojas después de Análisis_Estructurado
                    if poliza_data_actual:
                        df_polizas = pd.DataFrame(poliza_data_actual)

                        # Separar por tipo de documento
                        df_actuales = df_polizas[
                            df_polizas["Tipo de Documento"].str.lower() == "actual"
                        ].copy()
                        df_renovacion = df_polizas[
                            df_polizas["Tipo de Documento"].str.lower() == "renovacion"
                        ].copy()

                        # Función para crear tabla transpuesta consolidada
                        def crear_hoja_consolidada(df_actuales, df_renovacion):
                            if df_actuales.empty and df_renovacion.empty:
                                return

                            # Función auxiliar para procesar cada tipo de póliza
                            def procesar_poliza(df, tipo_poliza):
                                if df.empty:
                                    return None, None

                                # Obtener intereses únicos y sus valores
                                intereses_valores = {}
                                total_poliza = 0

                                for _, row in df.iterrows():
                                    interes = row["Interés Asegurado"]
                                    valor = row["Valor Asegurado"]
                                    total_poliza = row["Total Póliza"]
                                    intereses_valores[interes] = valor

                                # Crear estructura transpuesta
                                columnas = list(intereses_valores.keys()) + [
                                    "Total Póliza"
                                ]
                                valores = [
                                    f"${valor:,.0f}"
                                    for valor in intereses_valores.values()
                                ] + [f"${total_poliza:,.0f}"]

                                return columnas, valores

                            # Procesar ambos tipos de pólizas
                            columnas_actuales, valores_actuales = procesar_poliza(
                                df_actuales, "Actual"
                            )
                            columnas_renovacion, valores_renovacion = procesar_poliza(
                                df_renovacion, "Renovación"
                            )

                            # Crear DataFrame consolidado
                            datos_consolidados = []

                            # Agregar etiqueta y datos de pólizas actuales
                            if columnas_actuales and valores_actuales:
                                # Fila de etiqueta para pólizas actuales
                                fila_etiqueta_actual = ["PÓLIZAS ACTUALES"] + [""] * (
                                    len(columnas_actuales) - 1
                                )
                                datos_consolidados.append(fila_etiqueta_actual)

                                # Fila de encabezados
                                datos_consolidados.append(columnas_actuales)

                                # Fila de valores
                                datos_consolidados.append(valores_actuales)

                                # Fila de separación
                                datos_consolidados.append([""] * len(columnas_actuales))

                            # Agregar etiqueta y datos de pólizas de renovación
                            if columnas_renovacion and valores_renovacion:
                                # Ajustar longitud de columnas para que coincidan
                                max_cols = max(
                                    (
                                        len(columnas_actuales)
                                        if columnas_actuales
                                        else 0
                                    ),
                                    len(columnas_renovacion),
                                )

                                # Fila de etiqueta para pólizas de renovación
                                fila_etiqueta_renovacion = ["PÓLIZAS DE RENOVACIÓN"] + [
                                    ""
                                ] * (max_cols - 1)
                                datos_consolidados.append(fila_etiqueta_renovacion)

                                # Ajustar columnas de renovación si es necesario
                                columnas_renovacion_ajustadas = columnas_renovacion + [
                                    ""
                                ] * (max_cols - len(columnas_renovacion))
                                valores_renovacion_ajustados = valores_renovacion + [
                                    ""
                                ] * (max_cols - len(valores_renovacion))

                                # Fila de encabezados
                                datos_consolidados.append(columnas_renovacion_ajustadas)

                                # Fila de valores
                                datos_consolidados.append(valores_renovacion_ajustados)

                            # Crear DataFrame final
                            if datos_consolidados:
                                max_cols = max(len(fila) for fila in datos_consolidados)

                                # Ajustar todas las filas a la misma longitud
                                for i, fila in enumerate(datos_consolidados):
                                    if len(fila) < max_cols:
                                        datos_consolidados[i] = fila + [""] * (
                                            max_cols - len(fila)
                                        )

                                # Crear columnas genéricas
                                columnas_genericas = [
                                    f"Columna_{i+1}" for i in range(max_cols)
                                ]

                                df_consolidado = pd.DataFrame(
                                    datos_consolidados,
                                    columns=columnas_genericas,
                                )

                                # Exportar a Excel
                                df_consolidado.to_excel(
                                    writer,
                                    sheet_name="Polizas_Consolidadas",
                                    index=False,
                                    header=False,
                                )
                                format_worksheet(
                                    writer.sheets["Polizas_Consolidadas"],
                                    df_consolidado,
                                    "polizas",
                                )

                        # Crear hoja consolidada
                        crear_hoja_consolidada(df_actuales, df_renovacion)

                    # Hoja de primas eliminada según solicitud del usuario

                excel_data = output.getvalue()

                # Botón de descarga
                # Crear enlace de descarga que abre en nueva ventana
                b64_excel = base64.b64encode(excel_data).decode()
                href = f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}"

                # Botón con enlace que abre en nueva ventana y descarga automáticamente
                st.markdown(
                    f"""
                            <a href="{href}" download="analisis_polizas.xlsx" target="_blank" 
                               style="display: inline-block; padding: 0.5rem 1rem; background-color: #ff4b4b; 
                                      color: white; text-decoration: none; border-radius: 0.25rem; 
                                      font-weight: 600; border: none; cursor: pointer;"
                               onclick="setTimeout(function(){{window.close();}}, 1000);">
                                📊 Descargar Excel
                            </a>
                            """,
                    unsafe_allow_html=True,
                )

                # Limpieza automática de archivos procesados
                cleanup_processed_files(queue_items)

        else:
            st.warning("Por favor, sube al menos un archivo para procesar.")


if __name__ == "__main__":
    asyncio.run(main())
