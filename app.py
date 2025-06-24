import streamlit as st
from typing import TypedDict, Dict, List, Optional, Union
import os
import base64
import certifi
import aiohttp
import ssl
from tools import tools as tools_standard
import asyncio
import fitz  # PyMuPDF
from PIL import Image
import io
from jsonschema import validate, ValidationError
import json
import pandas as pd
from typing import Optional, List, TypedDict, cast


from typing import Optional, List, TypedDict


class CoberturaConMontoYObservacion(TypedDict, total=False):
    monto: Optional[str]
    observaciones: Optional[str]


class CoberturaConMontoYObservacionesList(TypedDict, total=False):
    monto: Optional[str]
    observaciones: Optional[List[str]]


class CoberturaSimpleConObservacion(TypedDict, total=False):
    monto: Optional[str]
    observaciones: Optional[str]


class CoberturasAmparoBasico(TypedDict, total=False):
    muerte_accidental: Optional[CoberturaSimpleConObservacion]
    incapacidad_total_y_permanente: Optional[CoberturaSimpleConObservacion]
    desmembracion_accidental: Optional[CoberturaSimpleConObservacion]
    auxilio_funerario_muerte_accidental: Optional[CoberturaSimpleConObservacion]
    gastos_medicos_por_accidente: Optional[CoberturaConMontoYObservacion]
    rehabilitacion_integral_por_accidente: Optional[CoberturaConMontoYObservacion]
    ambulancia_para_eventos: Optional[CoberturaConMontoYObservacionesList]


class Plazo(TypedDict, total=False):
    plazo: Optional[str]
    observaciones: Optional[str]


class PlazosDelSiniestro(TypedDict, total=False):
    plazo_aviso_siniestro: Optional[Plazo]
    plazo_pago_siniestro: Optional[Plazo]


class InfoArchivo(TypedDict):
    filename: str
    coberturas: CoberturasAmparoBasico
    plazos: PlazosDelSiniestro


class QueueItem(TypedDict):
    file_name: str
    file_extension: str
    file_path: str
    media_type: str


class SeguroOrchestrator:
    def __init__(
        self,
        api_key: str,  # API key de Anthropic
        model: str,  # Modelo de Claude a usar
    ):
        self.api_key = api_key
        self.model = model

    def format_docs(self, respuestas: List[dict]) -> List[InfoArchivo]:
        result: List[InfoArchivo] = []

        for r in respuestas:
            filename = r.get("file_name", "desconocido.pdf")
            coberturas = {}
            plazos = {}

            for entry in r.get("data", []):
                for item in entry.get("content", []):
                    name = item.get("name")
                    input_data = item.get("input", {})

                    if name == "coberturas_amparo_basico":
                        for k, v in input_data.items():
                            if isinstance(v, dict):
                                # Caso especial: ambulancia con lista de observaciones
                                if k == "ambulancia_para_eventos":
                                    obs = v.get("observaciones")
                                    if isinstance(obs, str):
                                        v["observaciones"] = [obs]
                                    elif obs is None:
                                        v["observaciones"] = []
                                    coberturas[k] = v

                                else:
                                    coberturas[k] = {
                                        "monto": v.get("monto"),
                                        "observaciones": v.get("observaciones"),
                                    }
                            else:
                                # Campos simples: wrap en objeto con solo monto
                                coberturas[k] = {
                                    "monto": v,
                                    "observaciones": None,
                                }

                    elif name == "plazos_del_siniestro":
                        for pk, pv in input_data.items():
                            if isinstance(pv, dict):
                                plazos[pk] = {
                                    "plazo": pv.get("plazo"),
                                    "observaciones": pv.get("observaciones"),
                                }

            result.append(
                {
                    "filename": filename,
                    "coberturas": cast(CoberturasAmparoBasico, coberturas),
                    "plazos": cast(PlazosDelSiniestro, plazos),
                }
            )

        return result

    # Hace requests a la API con reintentos
    async def make_api_request(
        self, url: str, headers: dict, data: dict, retries: int = 5
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
                            print(
                                f"API request failed with status {response.status}. Retrying in {sleep_time} seconds..."
                            )
                            await asyncio.sleep(sleep_time)
                        else:
                            print(
                                f"API request failed with status {response.status} - {await response.text()}"
                            )
                            raise ValueError(
                                f"Request failed with status {response.status}"
                            )
                except aiohttp.ClientError as e:
                    raise ValueError(f"Request error: {str(e)}")
        raise ValueError("Max retries exceeded.")

    async def tool_handler(
        self,
        tools: list,
        messages: list,
        tool_name: str,
        url: str = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        model: str = "gemini-2.5-flash",
        max_retries: int = 6,
    ):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "tool_choice": {
                "type": "function",
                "function": {"name": tool_name},
            },
        }
        schema = next(
            (
                tool["function"]["parameters"]
                for tool in tools
                if tool["function"]["name"] == tool_name
            ),
            None,
        )
        tool_output = None
        for attempt in range(0, max_retries):
            try:
                response = await self.make_api_request(
                    url=url,
                    headers=headers,
                    data=data,
                )

                if response["choices"][0]["message"]["tool_calls"][0]["function"][
                    "arguments"
                ]:
                    tool_output = json.loads(
                        response["choices"][0]["message"]["tool_calls"][0]["function"][
                            "arguments"
                        ]
                    )
                else:
                    raise ValueError("No tool output")

                usage = response["usage"]

                # print(f"Response for {tool_name}: {response}")

                validate(instance=tool_output, schema=schema)
                print("✅ Validation passed.")
                return {
                    "content": [
                        {
                            "name": tool_name,
                            "input": tool_output,
                        }
                    ],
                    "usage": {
                        "input_tokens": usage["prompt_tokens"],
                        "cache_creation_input_tokens": 0,
                        "cache_read_input_tokens": 0,
                        "output_tokens": usage["completion_tokens"],
                        "service_tier": "standard",
                    },
                }
            except ValidationError as e:
                # Notifica error de validación
                print(f"❌ Validation error for '{tool_name}': {e.message}")
                if attempt < max_retries:
                    print("🔄 Retrying...")
                    continue
                else:
                    print("❌ Max retries exceeded.")
                    raise ValueError(
                        f"Max retries exceeded for '{tool_name}'. Last error: {e.message}"
                    )
            except Exception as e:
                # Notifica error general
                print(f"❌ Unexpected error: {e}")
                if attempt < max_retries:
                    print("🔄 Retrying...")
                    continue
                else:
                    print("❌ Max retries exceeded.")
                    raise ValueError(
                        f"Max retries exceeded for '{tool_name}'. Last error: {e.message}"
                    )

    async def run_pdf_toolchain(
        self,
        item: QueueItem,
    ):
        print("PDF TOOLCHAIN")
        doc = fitz.open(item["file_path"])
        base64_images = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=150)  # convertimos a imagen

            # Convertimos el pixmap a imagen PIL
            img = Image.open(io.BytesIO(pix.tobytes("png")))

            # Guardamos en memoria y convertimos a base64
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
            base64_images.append(img_base64)

        image_messages = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"},
            }
            for img_b64 in base64_images
        ]

        response = await self.tool_handler(
            tools=[tool["data"] for tool in tools_standard],
            messages=[
                {
                    "role": "user",
                    "content": [
                        *image_messages,
                        {"type": "text", "text": tools_standard[0]["prompt"]},
                    ],
                }
            ],
            tool_name=tools_standard[0]["data"]["function"]["name"],
        )

        # Procesa con resto de herramientas en paralelo
        tasks = []
        for tool in tools_standard[1:]:
            tool_res = self.tool_handler(
                tools=[tool["data"] for tool in tools_standard],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            *image_messages,
                            {"type": "text", "text": tool["prompt"]},
                        ],
                    }
                ],
                tool_name=tool["data"]["function"]["name"],
            )
            tasks.append(tool_res)
        results = await asyncio.gather(*tasks)
        respuestas = [response] + results
        item["data"] = respuestas
        return item

    def pdf_to_base64(self, file_path: str) -> Union[str, None]:
        try:
            with open(file_path, "rb") as pdf_file:
                binary_data = pdf_file.read()
                base_64_encoded_data = base64.b64encode(binary_data)
                base64_string = base_64_encoded_data.decode("utf-8")
            return base64_string
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def save_uploaded_file(self, uploaded_file, save_path):
        # Create the full file path
        file_path = os.path.join(save_path, uploaded_file.name)

        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Save the file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path


def show_comparador_table(docs: List[dict]):
    st.subheader("📊 Comparador de Documentos")

    desired_order = [
        "muerte_accidental",
        "incapacidad_total_y_permanente",
        "desmembracion_accidental",
        "gastos_medicos_por_accidente",
        "auxilio_funerario_muerte_accidental",
        "rehabilitacion_integral_por_accidente",
        "ambulancia_para_eventos",
        "plazo_aviso_siniestro",
        "plazo_pago_siniestro",
    ]

    def format_value(value):
        if isinstance(value, dict):
            monto = value.get("monto") or value.get("plazo")
            observaciones = value.get("observaciones")

            if isinstance(observaciones, list):
                obs = " / ".join(observaciones)
            elif isinstance(observaciones, str):
                obs = observaciones
            else:
                obs = None

            if monto and obs:
                return f"{monto} ({obs})"
            elif monto:
                return monto
            elif obs:
                return f"({obs})"
            else:
                return "—"
        return str(value) if value else "—"

    # Unificamos datos por documento
    data = {}
    for doc in docs:
        col = {}
        col.update(doc.get("coberturas", {}))
        col.update(doc.get("plazos", {}))
        data[doc["filename"]] = col

    # Construir filas ordenadas
    rows = {}
    for key in desired_order:
        rows[key] = [format_value(data[file].get(key)) for file in data]

    df = pd.DataFrame(rows, index=data.keys()).T
    df.index.name = "Cobertura / Plazo"
    st.dataframe(df)


async def main():
    # Configuración de la página
    st.set_page_config(page_title="SeguroSmart", page_icon="🛡️", layout="wide")

    # Título y descripción
    st.sidebar.title("SeguroSmart 🛡️")
    st.sidebar.write(
        "SeguroSmart es una aplicación de inteligencia artificial diseñada para comparar pólizas de seguros y ayudarte a entender sus diferencias clave."
    )

    st.sidebar.subheader("Cargar Archivos PDF")
    uploaded_files = st.sidebar.file_uploader(
        "Arrastra y suelta tus archivos PDF aquí o haz clic para seleccionarlos",
        type=["pdf"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        st.sidebar.write("Archivos cargados:")
        for file in uploaded_files:
            st.sidebar.write(f"- {file.name}")

        if len(uploaded_files) < 2:
            st.sidebar.error(
                "Por favor, selecciona dos o más archivos PDF para comparar."
            )
        else:
            if st.sidebar.button("Iniciar Proceso", use_container_width=True):
                comparador = SeguroOrchestrator(
                    api_key=os.getenv("GOOGLE_API_KEY"),
                    model="gemini-2.5-flash",
                )

                st.sidebar.write("Proceso iniciado con los archivos:")
                tasks = []
                for file in uploaded_files:
                    saved_file_path = comparador.save_uploaded_file(file, "./downloads")
                    item = {
                        "file_name": file.name,
                        "file_extension": "pdf",
                        "file_path": saved_file_path,
                        "media_type": file.type,
                        "process_id": file.file_id,
                    }
                    task = comparador.run_pdf_toolchain(item)
                    tasks.append(task)

                respuestas = await asyncio.gather(*tasks)
                with st.expander("Respuestas Raw"):
                    st.write(respuestas)
                docs = comparador.format_docs(respuestas)
                with st.expander("Respuestas Formateadas"):
                    st.write(docs)
                show_comparador_table(docs)


if __name__ == "__main__":
    asyncio.run(main())
