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
                            "type": "object",
                            "description": "Cobertura por Gastos médicos por accidente.",
                            "properties": {
                                "monto": {
                                    "type": "string",
                                    "description": "Monto de la cobertura por Gastos médicos por accidente, si está indicado. Ej: 'AR$ 100.000' o 'USD 5,000'.",
                                    "nullable": True,
                                },
                                "observaciones": {
                                    "type": "string",
                                    "description": "Texto adicional relevante relacionado a esta cobertura, si hay detalles, condiciones o excepciones indicadas.",
                                    "nullable": True,
                                },
                            },
                            "required": [],
                            "additionalProperties": False,
                        },
                        "auxilio_funerario_muerte_accidental": {
                            "type": "string",
                            "description": "Monto de la cobertura por Auxilio funerario por muerte accidental, si está indicado.",
                            "nullable": True,
                        },
                        "rehabilitacion_integral_por_accidente": {
                            "type": "object",
                            "description": "Cobertura por Rehabilitación Integral por Accidente.",
                            "properties": {
                                "monto": {
                                    "type": "string",
                                    "description": "Monto de la cobertura por Rehabilitación Integral por Accidente, si está indicado. Ej: 'USD 3,000', 'AR$ 250.000'.",
                                    "nullable": True,
                                },
                                "observaciones": {
                                    "type": "string",
                                    "description": "Texto adicional relevante relacionado a esta cobertura, como condiciones específicas, exclusiones, plazos, etc.",
                                    "nullable": True,
                                },
                            },
                            "required": [],
                            "additionalProperties": False,
                        },
                        "ambulancia_para_eventos": {
                            "type": "object",
                            "description": "Cobertura por Ambulancia para Eventos.",
                            "properties": {
                                "monto": {
                                    "type": "string",
                                    "description": "Monto de la cobertura por Ambulancia para Eventos, si está indicado. Ej: 'USD 1,000' o 'AR$ 150.000'.",
                                    "nullable": True,
                                },
                                "observaciones": {
                                    "type": "array",
                                    "description": "Extrae únicamente las observaciones o condiciones asociadas a la cobertura de ambulancia para eventos. Enfócate en restricciones de uso (por ejemplo, 'una vez al año', 'máximo 2 usos'), modalidades de activación (como 'requiere autorización previa') y exclusiones específicas. No repitas el texto completo, solo extrae los fragmentos que describen estas limitaciones o condiciones.",
                                    "items": {"type": "string"},
                                    "nullable": True,
                                },
                            },
                            "required": [],
                            "additionalProperties": False,
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
                            "type": "object",
                            "description": "Plazo establecido para notificar o avisar del siniestro.",
                            "properties": {
                                "plazo": {
                                    "type": "string",
                                    "description": "Plazo explícito para avisar del siniestro. Ejemplo: '72 horas', '5 días hábiles', '10 días corridos'.",
                                    "nullable": True,
                                },
                                "observaciones": {
                                    "type": "string",
                                    "description": "Condiciones adicionales o notas relacionadas al aviso del siniestro (por ejemplo, desde cuándo corre el plazo, excepciones, etc.).",
                                    "nullable": True,
                                },
                            },
                            "required": ["plazo"],
                            "additionalProperties": False,
                        },
                        "plazo_pago_siniestro": {
                            "type": "object",
                            "description": "Plazo establecido para que la aseguradora pague el siniestro.",
                            "properties": {
                                "plazo": {
                                    "type": "string",
                                    "description": "Plazo explícito para el pago del siniestro. Ejemplo: '15 días hábiles', '30 días corridos'.",
                                    "nullable": True,
                                },
                                "observaciones": {
                                    "type": "string",
                                    "description": "Condiciones adicionales o notas relacionadas al plazo de pago (por ejemplo, desde la aceptación del reclamo, documentación completa, etc.).",
                                    "nullable": True,
                                },
                            },
                            "required": ["plazo"],
                            "additionalProperties": False,
                        },
                        "prima_por_asegurado": {
                            "type": "string",
                            "description": "Monto de la prima que corresponde a cada asegurado. Ejemplo: 'USD 10', 'AR$ 1.200'.",
                            "nullable": True,
                        },
                        "plazo_pago_primas": {
                            "type": "object",
                            "description": "Plazo establecido para el pago de primas.",
                            "properties": {
                                "plazo": {
                                    "type": "string",
                                    "description": "Plazo explícito para realizar el pago de la prima. Ejemplo: '30 días corridos', '15 días desde emisión'.",
                                    "nullable": True,
                                },
                                "observaciones": {
                                    "type": "string",
                                    "description": "Condiciones adicionales relacionadas con el plazo de pago de primas.",
                                    "nullable": True,
                                },
                            },
                            "required": ["plazo"],
                            "additionalProperties": False,
                        },
                        "forma_pago": {
                            "type": "string",
                            "description": "Método mediante el cual se debe pagar la prima. Ejemplo: 'Transferencia bancaria', 'Débito automático', 'Mercado Pago'.",
                            "nullable": True,
                        },
                    },
                    "required": [
                        "plazo_aviso_siniestro",
                        "plazo_pago_siniestro",
                        "prima_por_asegurado",
                        "plazo_pago_primas",
                        "forma_pago",
                    ],
                    "additionalProperties": False,
                },
            },
        },
    },
    {
        "prompt": "Extrae solo si están expresamente escritos en el texto los siguientes datos: 1) el reporte de novedades (cómo, cuándo o con qué frecuencia deben notificarse novedades del asegurado), 2) los requisitos de asegurabilidad (condiciones que debe cumplir una persona para ser asegurada, como edad, permanencia, salud, etc.), 3) las subjetividades (condiciones previas o requisitos que deben cumplirse para que la cobertura entre en vigencia), y 4) los clausulados aplicables (cláusulas contractuales específicas mencionadas como parte del contrato). No infieras, no completes por deducción, y no inventes información. Si alguno de estos puntos no se encuentra explícitamente en el texto, responde con: 'No se encontró información explícita'.",
        "data": {
            "type": "function",
            "function": {
                "name": "extraer_condiciones_y_clausulados",
                "description": "Identifica y extrae condiciones adicionales que afectan la validez o ejecución del seguro, como requisitos del asegurado, reportes obligatorios, cláusulas y restricciones sujetas al contrato.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reporte_novedades": {
                            "type": "object",
                            "description": "Condiciones relacionadas al reporte de novedades durante la vigencia del seguro.",
                            "properties": {
                                "reporte": {
                                    "type": "string",
                                    "description": "Texto que indique explícitamente las condiciones del reporte de novedades, como periodicidad u obligación de notificación.",
                                    "nullable": True,
                                },
                                "observaciones": {
                                    "type": "string",
                                    "description": "Notas adicionales, condiciones especiales o plazos asociados al reporte de novedades.",
                                    "nullable": True,
                                },
                            },
                            "required": [],
                            "additionalProperties": False,
                        },
                        "requisitos_asegurabilidad": {
                            "type": "string",
                            "description": "Requisitos que debe cumplir una persona para poder ser asegurada (por ejemplo, edad, salud, condiciones específicas).",
                            "nullable": True,
                        },
                        "subjetividades": {
                            "type": "array",
                            "description": "Lista de condiciones o requerimientos que deben cumplirse para que la cobertura esté completamente vigente.",
                            "items": {"type": "string"},
                            "nullable": True,
                        },
                        "clausulados_aplicables": {
                            "type": "array",
                            "description": "Lista exclusiva de cláusulas o condiciones contractuales que aplican a la póliza. Cada elemento debe ser únicamente el nombre, número o título de la cláusula, sin descripciones ni explicaciones adicionales.",
                            "items": {"type": "string"},
                            "nullable": True,
                        },
                    },
                    "required": [
                        "reporte_novedades",
                        "requisitos_asegurabilidad",
                        "subjetividades",
                        "clausulados_aplicables",
                    ],
                    "additionalProperties": False,
                },
            },
        },
    },
]
