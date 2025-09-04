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
            "type": "OBJECT",
            "properties": {
                "detalle_cobertura": {
                    "type": "ARRAY",
                    "description": "Listado de intereses asegurados y sus valores asegurados correspondientes.",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "interes_asegurado": {
                                "type": "STRING",
                                "description": "Descripción del interés asegurado (ejemplo: 'Edificio', 'Maquinaria', 'Vehículos').",
                            },
                            "valor_asegurado": {
                                "type": "NUMBER",
                                "description": "Valor monetario asegurado correspondiente al interés.",
                            },
                        },
                        "required": ["interes_asegurado", "valor_asegurado"],
                    },
                },
                "total_valores_asegurados": {
                    "type": "NUMBER",
                    "description": "Suma total de todos los valores asegurados listados en el detalle.",
                },
            },
            "required": ["detalle_cobertura", "total_valores_asegurados"],
        },
    },
    {
        "prompt": """
Analiza el documento proporcionado y extrae únicamente el valor de la prima.  

Devuelve solo el valor de la prima en el campo `prima`, sin agregar explicaciones ni otro contenido.
""",
        "data": {
            "type": "OBJECT",
            "properties": {
                # "prima": {
                #     "type": "NUMBER",
                #     "description": "Valor de la prima del documento (puede incluir impuestos según el caso).",
                # },
                "prima_sin_iva": {
                    "type": "NUMBER",
                    "description": "Valor de la prima sin aplicar IVA.",
                },
                "iva": {
                    "type": "NUMBER",
                    "description": "Monto correspondiente al IVA.",
                },
                "prima_con_iva": {
                    "type": "NUMBER",
                    "description": "Valor de la prima final con IVA incluido.",
                },
            },
            "required": ["prima_sin_iva", "iva", "prima_con_iva"],
        },
    },
]
