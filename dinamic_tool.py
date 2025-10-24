import streamlit as st
from collections import defaultdict
import re
from copy import deepcopy

# Standard library imports
from collections import defaultdict
from pandas.io.formats.style import Styler
import os
import ssl
from unittest import result
import uuid
import json
import base64
import logging
from io import BytesIO
from pathlib import Path
from typing import List, Optional, TypedDict, Dict, Literal
from dataclasses import dataclass, field
from streamlit.runtime.uploaded_file_manager import UploadedFile  # si usas Streamlit
import unicodedata

# Third party imports
import aiohttp
import certifi
import asyncio
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
import tempfile

load_dotenv()


def separar_por_archivo(data):
    grupos = defaultdict(list)
    adicionales_por_file = defaultdict(list)

    for item in data:
        archivo = item["Archivo"]
        if archivo == "adicional":
            file_name = item["file_name"]
            adicionales_por_file[file_name].append(item)
        else:
            grupos[archivo].append(item)

    # convertir adicionales_por_file a la forma de lista de listas
    grupos["adicional"] = list(adicionales_por_file.values())

    return dict(grupos)


def generar_prompt_unico(grouped_data):
    """
    Genera un único prompt que incluya actual, renovacion y todos los adicionales.
    """
    prompt = """
        Tengo varias listas de amparos de una póliza de seguros.

        Tu tarea es depurar y consolidar los nombres de los amparos según las siguientes reglas:

        1. **Agrupación por sinónimos o similitud semántica:**
        - Identifica amparos que representen el mismo concepto, aunque estén redactados de forma distinta.
        - Agrúpalos bajo un nombre común que los represente claramente.

        2. **Comparación entre listas:**
        - Compara los amparos de las listas entre sí.
        - Determina cuáles son equivalentes o semánticamente similares.
        - Unifica esos términos en grupos con un nombre representativo.

        3. **Resultado esperado:**
        - Devuelve una lista consolidada de amparos únicos, donde los sinónimos y subvariantes hayan sido agrupados.
        - Asegúrate de mantener los deducibles correspondientes y reflejar correctamente las agrupaciones.
        
        4. Si no se encuentra ningún resultado, devuelve una cadena vacía.

        Aquí están las listas de amparos:
        """

    # Actual
    if "actual" in grouped_data:
        prompt += f"\namparos_actuales = {grouped_data['actual']}\n"

    # Renovacion
    if "renovacion" in grouped_data:
        prompt += f"\namparos_renovacion = {grouped_data['renovacion']}\n"

    # Adicionales: cada subarray separado
    if "adicional" in grouped_data:
        for idx, subarray in enumerate(grouped_data["adicional"], start=1):
            prompt += f"\namparos_adicional_{idx} = {subarray}\n"

    return prompt


def _sanitize_key(name: str) -> str:
    # quitar extensión y normalizar a formato seguro para keys
    base = re.sub(r"\.pdf$", "", name, flags=re.IGNORECASE)
    base = re.sub(r"[^\w]+", "_", base)  # reemplaza cualquier char no alfanum por _
    base = base.strip("_").lower()
    return f"deducible_{base}" if base else "deducible_adicional"


def agregar_deducibles_adicionales(response_schema: dict, data: list) -> dict:
    """
    Agrega propiedades deducible_<file_name_sanitizado> por cada file_name
    presente en items con Archivo == "adicional". Las marca como required y
    las inserta justo después de deducible_renovacion en propertyOrdering.
    """
    schema = deepcopy(response_schema)
    items = schema.setdefault("items", {})
    properties = items.setdefault("properties", {})
    prop_order = items.setdefault("propertyOrdering", [])
    required = items.setdefault("required", [])

    # Obtener file_names únicos en orden de aparición
    vistos = []
    for d in data:
        if d.get("Archivo") == "adicional" and "file_name" in d:
            fn = d["file_name"]
            if fn not in vistos:
                vistos.append(fn)

    if not vistos:
        return schema  # no hay adicionales, devolver schema tal cual

    # posición base: justo después de 'deducible_renovacion' si existe, si no, al final antes de 'tipo' si existe
    try:
        base_index = prop_order.index("deducible_renovacion") + 1
    except ValueError:
        # si no existe, intentar antes de 'tipo'
        try:
            tipo_idx = prop_order.index("tipo")
            base_index = tipo_idx
        except ValueError:
            base_index = len(prop_order)

    # insertar cada nuevo campo manteniendo orden relativo
    for i, file_name in enumerate(vistos):
        key = _sanitize_key(file_name)
        # evitar sobrescribir si ya existe
        if key in properties:
            # si ya existe, no lo duplicamos, pero aseguramos que esté en required y ordering
            if key not in required:
                required.append(key)
            if key not in prop_order:
                prop_order.insert(base_index + i, key)
            continue

        properties[key] = {
            "type": "STRING",
            "description": f"Deducible que aplica para el documento adicional '{file_name}'.",
        }

        # agregar a required
        if key not in required:
            required.append(key)

        # insertar en propertyOrdering en posición base_index + i
        insert_pos = base_index + i
        if insert_pos > len(prop_order):
            prop_order.append(key)
        else:
            prop_order.insert(insert_pos, key)

    return schema


def mostrar_tabla_amparos(amparos):
    """
    Muestra una tabla en Streamlit con los datos de amparos.
    Cada fila incluye un índice automático.
    """
    # Convertimos a DataFrame
    df = pd.DataFrame(amparos)

    # Agregamos índice empezando desde 0
    df.reset_index(inplace=True)
    df.rename(columns={"index": "N°"}, inplace=True)

    # Convertimos la lista de tipos a string
    if "tipo" in df.columns:
        df["tipo"] = df["tipo"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else x
        )

    # Mostramos la tabla
    st.dataframe(df, use_container_width=True)


amparos_actuales = [
    {
        "amparo": "Incendio y/o Impacto Directo De Rayo",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Explosión",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Extensión de Amparos",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Explosión de Calderas u Otros Aparatos Generadores de Vapor",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Rotura Accidental De Vidrios",
        "deducible": "0,25 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Terremoto, Temblor De Tierra, Erupción Volcánica, Tsunami, Maremoto",
        "deducible": "2% del valor asegurable del artículo mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Anegación",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Daños Por Agua",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "AMIT Y Terrorismo",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "HMACC",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Productos Almacenados En Frigoríficos",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Daño Interno Equipos Eléctricos Y Electrónicos",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Equipo Electronico"],
    },
    {
        "amparo": "Portadores Externos de Datos",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Equipo Electronico"],
    },
    {
        "amparo": "Equipos Móviles Y Portátiles",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Equipo Electronico"],
    },
    {
        "amparo": "Incremento en Costos De Operación",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Daños por Fallas En Equipos De Climatización",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Rotura de Maquinaria"],
    },
    {
        "amparo": "Rotura De Maquinaria",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Rotura de Maquinaria"],
    },
    {
        "amparo": "Pérdida de Contenido en Tanques",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Deterioro de Bienes Refrigerados",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Hurto Calificado",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Sustracción"],
    },
    {
        "amparo": "Hurto Simple para Equipo Eléctrico Y Electrónico Fijo de Oficina",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Sustracción", "Equipo Electronico"],
    },
    {
        "amparo": "Bienes de Propiedad de Empleados del Asegurado",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Traslado Temporal de Bienes",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Transporte de Valores"],
    },
    {
        "amparo": "Construcciones y Montajes Nuevos",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Bienes a la Intemperie",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Actos de Autoridad",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Remoción de Escombros",
        "deducible": "Aplica el de la cobertura afectada",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Transporte De Valores",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Transporte de Valores"],
    },
    {
        "amparo": "Daños o pérdidas de Mercancías a Granel",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Manejo",
        "deducible": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Empleados de Carácter Temporal y/o de Firmas Especializadas",
        "deducible": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Empleados no Identificados",
        "deducible": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Bienes de Propiedad de Terceros",
        "deducible": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Protección para Depósitos Bancarios",
        "deducible": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Predios Labores y Operaciones",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Contratistas y Subcontratistas",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Patronal",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Vehículos Propios y no Propios",
        "deducible": "En exceso del SOAT y RCE autos mínimo 100.000.000/100.000.000/200.000.000 COP",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Propietarios, Arrendatarios y Poseedores",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Cruzada",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Parqueaderos",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
]

amparos_renovacion = [
    {
        "amparo": "Incendio y/o Impacto Directo De Rayo",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Explosión",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Explosión de Calderas u Otros Aparatos Generadores de Vapor",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Terremoto, Temblor De Tierra, Erupción Volcánica, Tsunami, Maremoto",
        "deducible": "3% del valor de la pérdida mínimo 1 S.M.M.L.V.",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Anegación",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Daños Por Agua",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "AMIT Y Terrorismo",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "HMACC",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Productos Almacenados En Frigoríficos",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Daño Interno Equipos Eléctricos Y Electrónicos",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Equipo Electronico"],
    },
    {
        "amparo": "Portadores Externos de Datos",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Equipo Electronico"],
    },
    {
        "amparo": "Equipos Móviles Y Portátiles",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Equipo Electronico"],
    },
    {
        "amparo": "Daños por Fallas En Equipos De Climatización",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Rotura de Maquinaria"],
    },
    {
        "amparo": "Rotura De Maquinaria",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Rotura de Maquinaria"],
    },
    {
        "amparo": "Pérdida de Contenido en Tanques",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Deterioro de Bienes Refrigerados",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Hurto Calificado",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Sustracción"],
    },
    {
        "amparo": "Hurto Simple para Equipo Eléctrico Y Electrónico Fijo de Oficina",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Sustracción", "Equipo Electronico"],
    },
    {
        "amparo": "Bienes de Propiedad de Empleados del Asegurado",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Traslado Temporal de Bienes",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Transporte de Valores"],
    },
    {
        "amparo": "Bienes a la Intemperie",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Actos de Autoridad",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Remoción de Escombros",
        "deducible": "Aplica el de la cobertura afectada",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Transporte De Valores",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Transporte de Valores"],
    },
    {
        "amparo": "Daños o pérdidas de Mercancías a Granel",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Manejo",
        "deducible": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Empleados de Carácter Temporal y/o de Firmas Especializadas",
        "deducible": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Empleados no Identificados",
        "deducible": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Bienes de Propiedad de Terceros",
        "deducible": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Protección para Depósitos Bancarios",
        "deducible": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Predios Labores y Operaciones",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Contratistas y Subcontratistas",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Patronal",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Vehículos Propios y no Propios",
        "deducible": "En exceso del SOAT y RCE autos mínimo 100.000.000/100.000.000/200.000.000 COP",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Propietarios, Arrendatarios y Poseedores",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Cruzada",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Parqueaderos",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
]

amparos_adicional = [
    {
        "amparo": "Incendio y/o rayo, Explosión, Extensión de amparos",
        "deducible": "5% PERD Min 1 (SMMLV)",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Daños por agua, Anegación, Deslizamiento, Avalancha",
        "deducible": "5% PERD Min 1 (SMMLV)",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Terremoto, Temblor y/o Erupción Volcánica, Maremoto, Tsunami",
        "deducible": "3% ABLE Min 3 (SMMLV)",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Huelga, Motín, Asonada, Conmoción Civil, Actos Mal Intencionados de Terceros",
        "deducible": "10% PERD Min 2 (SMMLV)",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Daño Interno - Equipos de Computo",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Equipo Electronico"],
    },
    {
        "amparo": "Hurto Calificado - Equipos",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Sustracción"],
    },
    {
        "amparo": "Hurto Calificado - Muebles y Enseres",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Sustracción"],
    },
    {
        "amparo": "Hurto Calificado - Maquinaria",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Sustracción"],
    },
    {
        "amparo": "Valores en Transito",
        "deducible": "20% PERD Min 3 (SMMLV)",
        "tipo": ["Transporte de Valores"],
    },
    {
        "amparo": "Dinero Efectivo y Títulos Valores",
        "deducible": "20% PERD Min 3 (SMMLV)",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Infidelidad de Empleados",
        "deducible": "10% PERD Min 1.5 (SMMLV)",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Responsabilidad Civil Extracontractual",
        "deducible": "10% PERD Min 2 (SMMLV)",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Rotura Accidental de Vidrios",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Remoción de Escombros",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Gastos Adicionales",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Gastos de Reposición de Archivo",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Daños a Calderas u otros Aparatos Generadores de Vapor",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Rotura de Maquinaria"],
    },
    {
        "amparo": "Propiedad personal de empleados",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Daños Estéticos",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Hurto de Equipos y Equipos de Computo de Oficina",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Sustracción"],
    },
    {
        "amparo": "Responsabilidad Civil Patronal",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Gastos Médicos y Hospitalarios",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Parqueaderos",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Contratistas y Subcontratistas",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Productos",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Vehículos Propios y No Propios",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil - Bienes Bajo Cuidado Tenencia y Control",
        "deducible": "10% PERD Min 2 (SMMLV)",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Costos de Proceso",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Cruzada",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Daños al Inmueble Arrendado",
        "deducible": "10% PERD Min 1 (SMMLV)",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Infidelidad - Empleados No Identificados",
        "deducible": "10% PERD Min 2 (SMMLV)",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Infidelidad - Empleados Temporales o de Firmas Especializadas",
        "deducible": "10% PERD Min 2 (SMMLV)",
        "tipo": ["Manejo de Dinero"],
    },
]

amparos_adicional_2 = [
    {
        "amparo": "Incendio y/o Impacto Directo De Rayo",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Explosión",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Extensión de Amparos",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Explosión de Calderas u Otros Aparatos Generadores de Vapor",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Rotura Accidental De Vidrios",
        "deducible": "0,25 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Terremoto, Temblor De Tierra, Erupción Volcánica, Tsunami, Maremoto",
        "deducible": "2% del valor asegurable del artículo mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Anegación",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Daños Por Agua",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "AMIT Y Terrorismo",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "HMACC",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Daño Interno Equipos Eléctricos Y Electrónicos",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Equipo Electronico"],
    },
    {
        "amparo": "Portadores Externos de Datos",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Equipo Electronico"],
    },
    {
        "amparo": "Incremento en Costos De Operación",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Daños por Fallas En Equipos De Climatización",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Rotura de Maquinaria"],
    },
    {
        "amparo": "Rotura De Maquinaria",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Rotura de Maquinaria"],
    },
    {
        "amparo": "Pérdida de Contenido en Tanques",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Hurto Calificado",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Sustracción"],
    },
    {
        "amparo": "Hurto Simple para Equipo Eléctrico Y Electrónico Fijo de Oficina",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Sustracción"],
    },
    {
        "amparo": "Bienes de Propiedad de Empleados del Asegurado",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Traslado Temporal de Bienes",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Construcciones y Montajes Nuevos",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Bienes a la Intemperie",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Actos de Autoridad",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Remoción de Escombros",
        "deducible": "Aplica el de la cobertura afectada",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Transporte De Valores",
        "deducible": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Transporte de Valores"],
    },
    {
        "amparo": "Manejo",
        "deducible": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Empleados de Carácter Temporal y/o de Firmas Especializadas",
        "deducible": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Empleados no Identificados",
        "deducible": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Bienes de Propiedad de Terceros",
        "deducible": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Protección para Depósitos Bancarios",
        "deducible": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Predios Labores y Operaciones",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Contratistas y Subcontratistas",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Patronal",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Vehículos Propios y no Propios",
        "deducible": "En exceso del SOAT y RCE autos mínimo 100.000.000/100.000.000/200.000.000 COP",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Propietarios, Arrendatarios y Poseedores",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Cruzada",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Parqueaderos",
        "deducible": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
]

amparos = (
    [
        {
            "Archivo": "actual",
            "Amparo": a["amparo"],
            "Deducible": a["deducible"],
            "Tipo": ", ".join(a["tipo"]),
            "file_name": "actual.pdf",
        }
        for a in amparos_actuales
        if "Incendio" in a["tipo"]
    ]
    + [
        {
            "Archivo": "renovacion",
            "Amparo": a["amparo"],
            "Deducible": a["deducible"],
            "Tipo": ", ".join(a["tipo"]),
            "file_name": "renovacion.pdf",
        }
        for a in amparos_renovacion
        if "Incendio" in a["tipo"]
    ]
    + [
        {
            "Archivo": "adicional",
            "Amparo": a["amparo"],
            "Deducible": a["deducible"],
            "Tipo": ", ".join(a["tipo"]),
            "file_name": "amparos_adicional_1.pdf",
        }
        for a in amparos_adicional
        if "Incendio" in a["tipo"]
    ]
    + [
        {
            "Archivo": "adicional",
            "Amparo": a["amparo"],
            "Deducible": a["deducible"],
            "Tipo": ", ".join(a["tipo"]),
            "file_name": "amparos_adicional_2.pdf",
        }
        for a in amparos_adicional_2
        if "Incendio" in a["tipo"]
    ]
)


response_schema = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "amparo": {
                "type": "STRING",
                "description": "Nombre del amparo o cobertura del seguro, por ejemplo 'Incendio y/o Impacto Directo de Rayo'.",
            },
            "deducible_actual": {
                "type": "STRING",
                "description": "Deducible que aplica actualmente para este amparo en la póliza vigente.",
            },
            "deducible_renovacion": {
                "type": "STRING",
                "description": "Deducible que aplicará al renovar la póliza para este amparo.",
            },
            "tipo": {
                "type": "ARRAY",
                "description": (
                    "Tipos de amparo: categorías del amparo según su cobertura. "
                    "Opciones disponibles: 'Incendio', 'Sustracción', 'Equipo Electrónico', "
                    "'Rotura de Maquinaria', 'Transporte de Valores', 'Manejo de Dinero', "
                    "'Responsabilidad Civil'."
                ),
                "items": {
                    "type": "STRING",
                    "enum": [
                        "Incendio",
                        "Sustracción",
                        "Equipo Electronico",
                        "Rotura de Maquinaria",
                        "Transporte de Valores",
                        "Manejo de Dinero",
                        "Responsabilidad Civil",
                    ],
                    "description": "Categoría específica del amparo.",
                },
            },
        },
        "required": [
            "amparo",
            "deducible_actual",
            "deducible_renovacion",
            "tipo",
        ],
        "propertyOrdering": [
            "amparo",
            "deducible_actual",
            "deducible_renovacion",
            "tipo",
        ],
        "description": "Objeto que representa un amparo de la póliza con sus deducibles y categorías.",
    },
    "description": "Lista de amparos que contiene información sobre deducibles actuales, de renovación y categorías.",
}


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
                                f"API request failed with status {response.status}. Retrying in {sleep_time} seconds... res: {response}"
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

    async def action_item_tool(self, prompt: str, responseSchema: dict):
        # URL del endpoint de la API de Gemini para generar contenido a partir del modelo especificado
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

        # Encabezados HTTP: autenticación con la clave de API y tipo de contenido JSON
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}

        # Cuerpo de la petición: incluye el PDF codificado y el texto del prompt
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",  # Forzar que la respuesta sea JSON
                "responseSchema": responseSchema,  # Esquema JSON que debe respetar la respuesta
            },
        }

        # Realizar la petición asíncrona a la API con reintentos incluidos
        response = await self.make_api_request(url, headers, payload, uuid.uuid4().hex)

        # Almacenar la respuesta de la API dentro del item bajo la clave "data"
        return response


orchestrator = InvoiceOrchestrator(
    api_key=os.getenv("GEMINI_API_KEY"),
    model="gemini-2.5-flash",
)


async def main():
    nueva_response_schema = agregar_deducibles_adicionales(response_schema, amparos)
    data = separar_por_archivo(amparos)
    prompt = generar_prompt_unico(data)

    with st.expander("Amparos"):
        st.write(data)

    with st.expander("Response Schema"):
        st.write(nueva_response_schema)

    with st.expander("Prompt"):
        st.write(prompt)

    if st.button("Comenzar"):
        response = await orchestrator.action_item_tool(prompt, nueva_response_schema)

        # 1️⃣ extraer el texto
        raw_text = response["candidates"][0]["content"]["parts"][0]["text"]

        # 2️⃣ convertirlo a lista de dicts (parsear el string JSON)
        result = json.loads(raw_text)

        with st.expander("Resultados"):
            st.write(result)

    if st.button("Debug"):
        amparos_debug = [
            {
                "amparo": "Incendio, Rayo, Explosión y Extensión de Amparos",
                "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_amparos_adicional_1": "5% PERD Min 1 (SMMLV)",
                "deducible_amparos_adicional_2": "5% del valor de la pérdida mínimo 1 SMMLV",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Rotura Accidental de Vidrios",
                "deducible_actual": "0,25 SMMLV",
                "deducible_renovacion": "No aplica",
                "deducible_amparos_adicional_1": "10% PERD Min 1 (SMMLV)",
                "deducible_amparos_adicional_2": "0,25 SMMLV",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Terremoto, Temblor, Erupción Volcánica, Tsunami y Maremoto",
                "deducible_actual": "2% del valor asegurable del artículo mínimo 1 SMMLV",
                "deducible_renovacion": "3% del valor de la pérdida mínimo 1 S.M.M.L.V.",
                "deducible_amparos_adicional_1": "3% ABLE Min 3 (SMMLV)",
                "deducible_amparos_adicional_2": "2% del valor asegurable del artículo mínimo 1 SMMLV",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Daños por Agua, Anegación, Deslizamiento y Avalancha",
                "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_amparos_adicional_1": "5% PERD Min 1 (SMMLV)",
                "deducible_amparos_adicional_2": "5% del valor de la pérdida mínimo 1 SMMLV",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "AMIT, Terrorismo, Huelga, Motín, Asonada y Conmoción Civil",
                "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_amparos_adicional_1": "10% PERD Min 2 (SMMLV)",
                "deducible_amparos_adicional_2": "5% del valor de la pérdida mínimo 1 SMMLV",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Pérdida o Deterioro de Bienes Refrigerados/en Frigoríficos",
                "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_amparos_adicional_1": "No aplica",
                "deducible_amparos_adicional_2": "No aplica",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Incremento en Costos de Operación",
                "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_renovacion": "No aplica",
                "deducible_amparos_adicional_1": "No aplica",
                "deducible_amparos_adicional_2": "10% del valor de la pérdida mínimo 1 SMMLV",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Pérdida de Contenido en Tanques",
                "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_amparos_adicional_1": "No aplica",
                "deducible_amparos_adicional_2": "10% del valor de la pérdida mínimo 1 SMMLV",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Construcciones y Montajes Nuevos",
                "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_renovacion": "No aplica",
                "deducible_amparos_adicional_1": "No aplica",
                "deducible_amparos_adicional_2": "5% del valor de la pérdida mínimo 1 SMMLV",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Bienes a la Intemperie",
                "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_amparos_adicional_1": "No aplica",
                "deducible_amparos_adicional_2": "5% del valor de la pérdida mínimo 1 SMMLV",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Actos de Autoridad",
                "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_amparos_adicional_1": "No aplica",
                "deducible_amparos_adicional_2": "5% del valor de la pérdida mínimo 1 SMMLV",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Remoción de Escombros",
                "deducible_actual": "Aplica el de la cobertura afectada",
                "deducible_renovacion": "Aplica el de la cobertura afectada",
                "deducible_amparos_adicional_1": "10% PERD Min 1 (SMMLV)",
                "deducible_amparos_adicional_2": "Aplica el de la cobertura afectada",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Daños o Pérdidas de Mercancías a Granel",
                "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
                "deducible_amparos_adicional_1": "No aplica",
                "deducible_amparos_adicional_2": "No aplica",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Gastos Adicionales",
                "deducible_actual": "No aplica",
                "deducible_renovacion": "No aplica",
                "deducible_amparos_adicional_1": "10% PERD Min 1 (SMMLV)",
                "deducible_amparos_adicional_2": "No aplica",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Gastos de Reposición de Archivo",
                "deducible_actual": "No aplica",
                "deducible_renovacion": "No aplica",
                "deducible_amparos_adicional_1": "10% PERD Min 1 (SMMLV)",
                "deducible_amparos_adicional_2": "No aplica",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Bienes de Propiedad de Empleados",
                "deducible_actual": "No aplica",
                "deducible_renovacion": "No aplica",
                "deducible_amparos_adicional_1": "10% PERD Min 1 (SMMLV)",
                "deducible_amparos_adicional_2": "5% del valor de la pérdida mínimo 1 SMMLV",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Daños Estéticos",
                "deducible_actual": "No aplica",
                "deducible_renovacion": "No aplica",
                "deducible_amparos_adicional_1": "10% PERD Min 1 (SMMLV)",
                "deducible_amparos_adicional_2": "No aplica",
                "tipo": ["Incendio"],
            },
            {
                "amparo": "Traslado Temporal de Bienes",
                "deducible_actual": "No aplica",
                "deducible_renovacion": "No aplica",
                "deducible_amparos_adicional_1": "No aplica",
                "deducible_amparos_adicional_2": "5% del valor de la pérdida mínimo 1 SMMLV",
                "tipo": ["Incendio"],
            },
        ]
        st.title("📋 Tabla de Amparos")
        mostrar_tabla_amparos(amparos_debug)


if __name__ == "__main__":
    asyncio.run(main())
