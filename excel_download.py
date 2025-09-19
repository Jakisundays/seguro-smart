import streamlit as st
import base64
import tempfile
import os

from excel_factory import (
    generar_excel_analisis_polizas,
    poliza_actual,
    poliza_renovacion,
    riesgos_actuales,
    riesgos_renovacion,
    amparos_actuales,
    amparos_renovacion,
    amparos_adicionales,
)

st.set_page_config(page_title="Descarga de Excel - SeguroSmart", page_icon="📊", layout="centered")

st.title("Descargar Excel de Análisis de Pólizas")
st.write(
    "Genera el archivo Excel utilizando los datos definidos en excel_factory.py y descárgalo en una nueva pestaña."
)

# Estilos para que el enlace se vea como un botón real
st.markdown(
    """
    <style>
    a.download-btn{
      display:inline-flex;align-items:center;gap:.5rem;
      padding:.6rem 1rem;background:#2E75B6;color:#fff;text-decoration:none;
      border-radius:.5rem;font-weight:600;box-shadow:0 1px 2px rgba(0,0,0,.1);
      transition:background .2s ease, transform .05s ease, box-shadow .2s ease;
      cursor:pointer;
    }
    a.download-btn:hover{background:#255e91;box-shadow:0 2px 6px rgba(0,0,0,.15);}
    a.download-btn:active{transform:translateY(1px);}
    </style>
    """,
    unsafe_allow_html=True,
)

if st.button("Generar Excel", type="primary"):
    with st.spinner("Generando Excel..."):
        tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        tmp_path = tmp.name
        tmp.close()
        try:
            # Generar el Excel usando la función ya existente en excel_factory.py
            output_path = generar_excel_analisis_polizas(
                poliza_actual=poliza_actual,
                poliza_renovacion=poliza_renovacion,
                riesgos_actuales=riesgos_actuales,
                riesgos_renovacion=riesgos_renovacion,
                amparos_actuales=amparos_actuales,
                amparos_renovacion=amparos_renovacion,
                amparos_adicionales=amparos_adicionales,
                output_path=tmp_path,
            )

            # Leer bytes y crear un enlace <a> con target="_blank"
            with open(output_path, "rb") as f:
                excel_bytes = f.read()
            b64_excel = base64.b64encode(excel_bytes).decode()
            href = (
                "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64," + b64_excel
            )

            st.success("Excel generado correctamente.")
            st.markdown(
                f'''
                <a class="download-btn" href="{href}" download="reporte_polizas_riesgos.xlsx" target="_blank" role="button" aria-label="Descargar Excel de análisis">
                  📥 <span>Descargar Excel</span>
                </a>
                ''',
                unsafe_allow_html=True,
            )
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass