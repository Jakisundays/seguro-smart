tools = [
    {
        "prompt": (
            "Extrae los montos explícitos de las coberturas incluidas en el Amparo Básico. "
            "Cada cobertura debe estar como campo independiente. "
            "Devuelve el monto tal como aparece (por ejemplo: 'USD 5.000' o 'AR$ 1.000.000'). "
            "NO INFIERAS: si la cobertura no está mencionada o no tiene monto claro, no devuelvas ningún valor para ese campo."
        ),
        "data": {
            "type": "function",
            "function": {
                "name": "coberturas_amparo_basico",
                "description": "Extrae montos asociados a cada cobertura estándar del Amparo Básico, si están explícitamente indicados.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "muerte_accidental": {
                            "type": "string",
                            "description": "Monto de la cobertura por Muerte accidental, si está indicado.",
                            "nullable": True,
                        },
                        "incapacidad_total_y_permanente": {
                            "type": "string",
                            "description": "Monto de la cobertura por Incapacidad Total y Permanente, si está indicado.",
                            "nullable": True,
                        },
                        "desmembracion_accidental": {
                            "type": "string",
                            "description": "Monto de la cobertura por Desmembración accidental, si está indicado.",
                            "nullable": True,
                        },
                        "gastos_medicos_por_accidente": {
                            "type": "string",
                            "description": "Monto de la cobertura por Gastos médicos por accidente, si está indicado.",
                            "nullable": True,
                        },
                        "auxilio_funerario_muerte_accidental": {
                            "type": "string",
                            "description": "Monto de la cobertura por Auxilio funerario por muerte accidental, si está indicado.",
                            "nullable": True,
                        },
                        "rehabilitacion_integral_por_accidente": {
                            "type": "string",
                            "description": "Monto de la cobertura por Rehabilitación Integral por Accidente, si está indicado.",
                            "nullable": True,
                        },
                        "ambulancia_para_eventos": {
                            "type": "string",
                            "description": "Monto de la cobertura por Ambulancia para Eventos, si está indicado.",
                            "nullable": True,
                        },
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
    },
    {
        "prompt": (
            "Extrae los plazos explícitamente indicados para:\n"
            "- Avisar del siniestro\n"
            "- Pagar el siniestro\n\n"
            "Devuelve los valores exactamente como están redactados en el documento, incluyendo número y unidad de tiempo (por ejemplo: '72 horas', '15 días hábiles', '10 días corridos').\n"
            "NO INFIERAS NADA: Si no está expresamente escrito el plazo, no devuelvas ningún valor para ese campo."
        ),
        "data": {
            "type": "function",
            "function": {
                "name": "plazos_del_siniestro",
                "description": "Extrae los plazos establecidos para el aviso del siniestro y el pago del siniestro, si están presentes de forma explícita.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "plazo_aviso_siniestro": {
                            "type": "string",
                            "description": "Plazo explícito indicado para notificar o avisar del siniestro, por ejemplo: '72 horas', '5 días'.",
                            "nullable": True,
                        },
                        "plazo_pago_siniestro": {
                            "type": "string",
                            "description": "Plazo explícito indicado para que la aseguradora pague el siniestro, por ejemplo: '15 días hábiles', '30 días corridos'.",
                            "nullable": True,
                        },
                    },
                    "required": ["plazo_aviso_siniestro", "plazo_pago_siniestro"],
                    "additionalProperties": False,
                },
            },
        },
    },
]
