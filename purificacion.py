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


def render_tablas_por_tipo(data):
    """
    Renderiza una tabla por cada tipo de amparo en Streamlit, numerando desde 0.

    Args:
        data (list[dict]): Lista de amparos con las llaves:
            - amparo (str)
            - deducible_actual (str)
            - deducible_renovacion (str)
            - tipo (list[str])
    """
    df = pd.DataFrame(data)

    # Normalizar el campo tipo (por si viene como string)
    df["tipo"] = df["tipo"].apply(lambda x: x if isinstance(x, list) else [x])

    # Extraer tipos únicos
    tipos_unicos = sorted({t for tipos in df["tipo"] for t in tipos})

    st.title("📘 Condiciones por Tipo de Amparo")

    for tipo in tipos_unicos:
        st.markdown(f"### 🟦 {tipo.upper()}")

        # Filtrar los amparos del tipo actual
        df_tipo = df[df["tipo"].apply(lambda x: tipo in x)][
            ["amparo", "deducible_actual", "deducible_renovacion"]
        ].reset_index(drop=True)

        # Agregar columna de número (empezando en 0)
        df_tipo.insert(0, "#", df_tipo.index)

        # Renombrar columnas
        df_tipo = df_tipo.rename(
            columns={
                "amparo": "Amparo",
                "deducible_actual": "Condiciones Actuales",
                "deducible_renovacion": "Condiciones de Renovación",
            }
        )

        # Mostrar tabla en Streamlit
        st.dataframe(df_tipo, hide_index=True, use_container_width=True)

        st.divider()


# Configurar logger
app_logger = logging.getLogger(__name__)
app_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
app_logger.addHandler(handler)


def amparos_a_reporte(amparos: list) -> pd.DataFrame:
    # Convertimos a DataFrame
    df = pd.DataFrame(amparos)

    # Explode si hay varios tipos
    df["Tipo"] = df["Tipo"].str.split(r",\s*")
    df = df.explode("Tipo")

    # Pivot: filas=Amparo, columnas=[Tipo, Archivo]
    df_pivot = df.pivot_table(
        index="Amparo", columns=["Tipo", "Archivo"], values="Deducible", aggfunc="first"
    )

    # Optional: ordenar las columnas por Tipo y Archivo
    df_pivot = df_pivot.sort_index(axis=1, level=[0, 1])

    # Reset para que Amparo sea columna normal
    df_pivot = df_pivot.reset_index()

    return df_pivot


def pivot_amparos(amparos: List[Dict]) -> List[Dict]:
    """
    Devuelve una lista donde cada amparo tiene los tipos como claves,
    y cada tipo contiene los archivos y sus deducibles.
    """
    resultado = defaultdict(lambda: defaultdict(dict))

    for a in amparos:
        amparo = a["Amparo"]
        archivos = [t.strip() for t in a["Tipo"].split(",")]
        archivo_actual = a["Archivo"]
        deducible = a["Deducible"]

        for tipo in archivos:
            resultado[amparo][tipo][archivo_actual] = deducible

    # Convertimos a lista final
    final = []
    for amparo, tipos_dict in resultado.items():
        entry = {"amparo": amparo}
        for tipo, archivos_dict in tipos_dict.items():
            entry[tipo] = archivos_dict
        final.append(entry)

    return final


def amparos_a_dataframe(amparos: list) -> pd.DataFrame:
    """
    Convierte la lista de amparos en un DataFrame pivotado:
    - Cada fila: un Amparo
    - Columnas: archivo+tipo con su deducible
    """
    # Convertimos la lista en DataFrame
    df = pd.DataFrame(amparos)

    # Si 'Tipo' tiene varios valores separados por coma, los expandimos
    df["Tipo"] = df["Tipo"].str.split(r",\s*")
    df = df.explode("Tipo")  # Cada tipo en su propia fila

    # Pivotamos: filas=Amparo, columnas=(Tipo, Archivo), valores=Deducible
    df_pivot = df.pivot_table(
        index="Amparo",
        columns=["Tipo", "Archivo"],
        values="Deducible",
        aggfunc="first",  # si hay duplicados, toma el primero
    )

    # Opcional: aplanar columnas MultiIndex
    df_pivot.columns = [f"{tipo}_{archivo}" for tipo, archivo in df_pivot.columns]
    df_pivot = df_pivot.reset_index()

    return df_pivot


def tablas_por_tipo(amparos: list) -> Dict[str, pd.DataFrame]:
    """
    Genera un dict de DataFrames, uno por cada 'Tipo'.
    - Filas: 'Amparo'
    - Columnas: un campo por cada 'Archivo' (actual, renovacion, otros)
    - Valores: 'Deducible'
    """
    df = pd.DataFrame(amparos)
    # Expandir 'Tipo' si trae múltiples valores separados por comas
    df["Tipo"] = df["Tipo"].str.split(r",\s*")
    df = df.explode("Tipo")

    tablas: Dict[str, pd.DataFrame] = {}

    # Conjunto global de archivos presentes en todo el dataset
    all_archivos = [a for a in df["Archivo"].dropna().unique().tolist()]

    # Definir orden consistente de columnas de archivos (Amparo + actual/renovacion + otros)
    def columnas_ordenadas_completas() -> List[str]:
        base = ["actual", "renovacion"]
        otros = [c for c in all_archivos if c not in base]
        return ["Amparo"] + [c for c in base if c in all_archivos] + sorted(otros)

    for tipo in sorted(df["Tipo"].dropna().unique()):
        df_tipo = df[df["Tipo"] == tipo]
        piv = df_tipo.pivot_table(
            index="Amparo", columns="Archivo", values="Deducible", aggfunc="first"
        )
        piv = piv.reset_index()
        # Ordenar filas por Amparo para lectura lógica
        piv = piv.sort_values(by="Amparo", kind="stable")
        # Asegurar presencia de todas las columnas de archivos, aunque no haya respuesta
        for col in columnas_ordenadas_completas():
            if col != "Amparo" and col not in piv.columns:
                piv[col] = ""
        # Reordenar columnas según criterio completo
        piv = piv[columnas_ordenadas_completas()]
        # Rellenar vacíos con cadena vacía para "sin respuesta"
        piv = piv.fillna("")
        tablas[tipo] = piv

    return tablas


def estilo_tabla(df: pd.DataFrame) -> Styler:
    """Aplica un estilo consistente (alineación, encabezados) a la tabla.
    Evita el uso de métodos no disponibles del Styler entre versiones de pandas.
    """
    styler = df.style.set_properties(**{"text-align": "left"}).set_table_styles(
        [
            {
                "selector": "th",
                "props": "text-align: left; font-weight: bold; background-color: #f5f5f5;",
            },
            {"selector": "td", "props": "vertical-align: top;"},
        ]
    )
    # No ocultamos el índice vía API para evitar incompatibilidades.
    # Si se desea ocultar el índice, usar df.reset_index(drop=True) antes de estilizar
    # o st.dataframe(df, hide_index=True) cuando no se use Styler.
    return styler


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

amparos = [
    {
        "Archivo": "actual",
        "Amparo": a["amparo"],
        "Deducible": a["deducible"],
        "Tipo": ", ".join(a["tipo"]),
    }
    for a in amparos_actuales
] + [
    {
        "Archivo": "renovacion",
        "Amparo": a["amparo"],
        "Deducible": a["deducible"],
        "Tipo": ", ".join(a["tipo"]),
    }
    for a in amparos_renovacion
]

amparos_resultados = [
    {
        "amparo": "AMIT Y Terrorismo",
        "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Actos de Autoridad",
        "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Anegación",
        "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Bienes a la Intemperie",
        "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Bienes de Propiedad de Empleados del Asegurado",
        "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Bienes de Propiedad de Terceros",
        "deducible_actual": "10% del valor de la pérdida mínimo 2 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Construcciones y Montajes Nuevos",
        "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "No aplica",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Contratistas y Subcontratistas",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Daño Interno Equipos Eléctricos Y Electrónicos",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Equipo Electronico"],
    },
    {
        "amparo": "Daños Por Agua",
        "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Daños por Fallas En Equipos De Climatización",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Rotura de Maquinaria"],
    },
    {
        "amparo": "Daños o pérdidas de Mercancías a Granel",
        "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Deterioro de Bienes Refrigerados",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Empleados de Carácter Temporal y/o de Firmas Especializadas",
        "deducible_actual": "10% del valor de la pérdida mínimo 2 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Empleados no Identificados",
        "deducible_actual": "10% del valor de la pérdida mínimo 2 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Equipos Móviles Y Portátiles",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Equipo Electronico"],
    },
    {
        "amparo": "Explosión",
        "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Explosión de Calderas u Otros Aparatos Generadores de Vapor",
        "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Extensión de Amparos",
        "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "No aplica",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "HMACC",
        "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Hurto Calificado",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Sustracción"],
    },
    {
        "amparo": "Hurto Simple para Equipo Eléctrico Y Electrónico Fijo de Oficina",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Sustracción", "Equipo Electronico"],
    },
    {
        "amparo": "Incendio y/o Impacto Directo De Rayo",
        "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Incremento en Costos De Operación",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "No aplica",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Manejo",
        "deducible_actual": "10% del valor de la pérdida mínimo 2 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Pérdida de Contenido en Tanques",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Portadores Externos de Datos",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Equipo Electronico"],
    },
    {
        "amparo": "Predios Labores y Operaciones",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Productos Almacenados En Frigoríficos",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Protección para Depósitos Bancarios",
        "deducible_actual": "10% del valor de la pérdida mínimo 2 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 2 SMMLV",
        "tipo": ["Manejo de Dinero"],
    },
    {
        "amparo": "Propietarios, Arrendatarios y Poseedores",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Remoción de Escombros",
        "deducible_actual": "Aplica el de la cobertura afectada",
        "deducible_renovacion": "Aplica el de la cobertura afectada",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Responsabilidad Civil Cruzada",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Parqueaderos",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Responsabilidad Civil Patronal",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Responsabilidad Civil"],
    },
    {
        "amparo": "Rotura Accidental De Vidrios",
        "deducible_actual": "0,25 SMMLV",
        "deducible_renovacion": "No aplica",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Rotura De Maquinaria",
        "deducible_actual": "10% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "10% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Rotura de Maquinaria"],
    },
    {
        "amparo": "Terremoto, Temblor De Tierra, Erupción Volcánica, Tsunami, Maremoto",
        "deducible_actual": "2% del valor asegurable del artículo mínimo 1 SMMLV",
        "deducible_renovacion": "3% del valor de la pérdida mínimo 1 S.M.M.L.V.",
        "tipo": ["Incendio"],
    },
    {
        "amparo": "Transporte De Valores",
        "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Transporte de Valores"],
    },
    {
        "amparo": "Traslado Temporal de Bienes",
        "deducible_actual": "5% del valor de la pérdida mínimo 1 SMMLV",
        "deducible_renovacion": "5% del valor de la pérdida mínimo 1 SMMLV",
        "tipo": ["Transporte de Valores"],
    },
    {
        "amparo": "Vehículos Propios y no Propios",
        "deducible_actual": "En exceso del SOAT y RCE autos mínimo 100.000.000/100.000.000/200.000.000 COP",
        "deducible_renovacion": "En exceso del SOAT y RCE autos mínimo 100.000.000/100.000.000/200.000.000 COP",
        "tipo": ["Responsabilidad Civil"],
    },
]

# df_amparos_actuales = pd.DataFrame(
#     [
#         {
#             "Amparo": a["amparo"],
#             "Deducible": a["deducible"],
#             "Tipo": ", ".join(a["tipo"]),
#         }
#         for a in amparos_actuales
#     ]
# )
# st.header("AMPAROS ACTUALES")
# st.dataframe(df_amparos_actuales)
# st.write("---")


# df_amparos_renovacion = pd.DataFrame(
#     [
#         {
#             "Amparo": a["amparo"],
#             "Deducible": a["deducible"],
#             "Tipo": ", ".join(a["tipo"]),
#         }
#         for a in amparos_renovacion
#     ]
# )
# st.header("AMPAROS Renovacion")
# st.dataframe(df_amparos_renovacion)
# st.write("---")


# st.header("AMPAROS")


# amparos.extend(
#     [
#         {
#             "Archivo": "a",
#             "Amparo": "aaaaaaa",
#             "Deducible": "aaaaa",
#             "Tipo": "aaaaa",
#         },
#         {
#             "Archivo": "b",
#             "Amparo": "aaaaaaa",
#             "Deducible": "aaaaa",
#             "Tipo": "aaaaa",
#         },
#     ]
# )

# df_amparos = pd.DataFrame(amparos)
# st.dataframe(df_amparos)

# st.write("---")


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
    # Reemplazar sección final de render por tablas separadas por tipo
    st.header("Tablas por Tipo")
    _tablas = tablas_por_tipo(amparos)
    for _tipo in sorted(_tablas.keys()):
        st.subheader(f"Tipo: {_tipo}")
        _df = _tablas[_tipo]
        st.dataframe(estilo_tabla(_df), use_container_width=True)
        st.write("---")
    st.write("")

    if st.button("Purificar", use_container_width=True, type="primary"):
        prompt = f"""
                Tengo dos listas de amparos: `amparos_actuales` y `amparos_renovacion`.

                Tu tarea es depurar y consolidar los nombres de los amparos según las siguientes reglas:

                1. **Agrupación por sinónimos o similitud semántica:**
                - Identifica amparos que representen el mismo concepto, aunque estén redactados de forma distinta.
                - Agrúpalos bajo un nombre común que los represente claramente.

                2. **Comparación entre listas:**
                - Compara los amparos de ambas listas.
                - Determina cuáles son equivalentes o semánticamente similares.
                - Unifica esos términos en grupos con un nombre representativo.

                3. **Resultado esperado:**
                - Devuelve una lista consolidada de amparos únicos, donde los sinónimos y subvariantes hayan sido agrupados.
                - Asegúrate de mantener los deducibles correspondientes y reflejar correctamente las agrupaciones.

                Aquí están las listas:
                amparos_actuales = {amparos_actuales}
                amparos_renovacion = {amparos_renovacion}
                """

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
        res = await orchestrator.action_item_tool(
            prompt=prompt,
            responseSchema=response_schema,
        )
        result = json.loads(
            res.get("candidates")[0].get("content").get("parts")[0].get("text")
        )

        with st.expander("Resultados"):
            st.write(result)

        render_tablas_por_tipo(result)

    if st.button("Debug", use_container_width=True, type="tertiary"):
        with st.expander("Amparos results"):
            st.write(amparos_resultados)
        render_tablas_por_tipo(amparos_resultados)


if __name__ == "__main__":
    asyncio.run(main())
