tools = [
    {
        "prompt": """
Analiza el documento proporcionado y extrae el detalle de la cobertura.  
Por cada interés asegurado identificado, devuelve:  
- el nombre o descripción del interés asegurado (por ejemplo: 'Edificio', 'Maquinaria', 'Vehículos'),  
- el valor asegurado correspondiente.  

Además, calcula el total de todos los valores asegurados y devuélvelo en el campo `total_valores_asegurados`.  

Devuelve únicamente los campos `detalle_cobertura` y `total_valores_asegurados` en el formato solicitado, sin explicaciones adicionales.
""",
        "data": {
            "type": "function",
            "function": {
                "name": "extraer_detalle_cobertura",
                "description": "Extrae el detalle de la cobertura, con los intereses asegurados, sus valores asegurados y el total de todos los valores.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "detalle_cobertura": {
                            "type": "array",
                            "description": "Listado de intereses asegurados y sus valores asegurados correspondientes.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "interes_asegurado": {
                                        "type": "string",
                                        "description": "Descripción del interés asegurado (ejemplo: 'Edificio', 'Maquinaria', 'Vehículos').",
                                    },
                                    "valor_asegurado": {
                                        "type": "number",
                                        "description": "Valor monetario asegurado correspondiente al interés.",
                                        "nullable": True,
                                    },
                                },
                                "required": ["interes_asegurado", "valor_asegurado"],
                                "additionalProperties": False,
                            },
                            "nullable": True,
                        },
                        "total_valores_asegurados": {
                            "type": "number",
                            "description": "Suma total de todos los valores asegurados listados en el detalle.",
                            "nullable": True,
                        },
                    },
                    "required": ["detalle_cobertura", "total_valores_asegurados"],
                    "additionalProperties": False,
                },
            },
        },
    },
    {
        "prompt": """
Analiza el documento proporcionado y extrae únicamente el valor de la prima.  

Devuelve solo el valor de la prima en el campo `prima`, sin agregar explicaciones ni otro contenido.
""",
        "data": {
            "type": "function",
            "function": {
                "name": "extraer_prima_documento",
                "description": "Extrae únicamente el valor de la prima del documento proporcionado.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prima": {
                            "type": "number",
                            "description": "Valor de la prima del documento.",
                            "nullable": True,
                        }
                    },
                    "required": ["prima"],
                    "additionalProperties": False,
                },
            },
        },
    },
]
