tools = [
    {
        "prompt": """
Analiza el documento proporcionado y extrae la siguiente información:

Detalle de cobertura: listado de intereses asegurados con su nombre (`interes_asegurado`) y valor (`valor_asegurado`).

Amparos: por cada amparo identificado, devuelve el nombre (`amparo`) y el deducible (`deducible`).

Total de valores asegurados: calcula y devuelve en el campo `total_valores_asegurados`.

Riesgos: por cada riesgo identificado, devuelve:
- La dirección completa (`ubicacion`).
- Su `detalle_cobertura` con los intereses asegurados y sus valores.

No inventes información ni calcules valores que no estén presentes en el documento.  
Devuelve únicamente los campos `detalle_cobertura`, `amparos`, `total_valores_asegurados` y `riesgos` en el formato solicitado, sin explicaciones adicionales.
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
                "amparos": {
                    "type": "ARRAY",
                    "description": "Listado de amparos incluidos en la póliza, con su límite por vigencia.",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "amparo": {
                                "type": "STRING",
                                "description": "Nombre del amparo o interés a cubrir.",
                            },
                            "deducible": {
                                "type": "STRING",
                                "description": "Porcentaje o valor mínimo que debe asumir el asegurado en caso de una pérdida o siniestro cubierto antes de que la aseguradora realice el pago correspondiente. Generalmente expresado como un porcentaje del valor de la pérdida con un monto mínimo en SMLMV.",
                            },
                        },
                        "required": ["amparo", "deducible"],
                    },
                },
                "riesgos": {
                    "type": "ARRAY",
                    "description": "Listado de riesgos asegurados, identificado por su calle y con los valores asegurados por tipo de interés.",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "ubicacion": {
                                "type": "STRING",
                                "description": "Dirección completa tal cual aparece en el documento (opcional).",
                            },
                            "detalle_cobertura": {
                                "type": "ARRAY",
                                "description": "Intereses asegurados y valores asociados para este riesgo específico.",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "interes_asegurado": {
                                            "type": "STRING",
                                            "description": "Descripción del interés asegurado (ej.: 'Edificio', 'Maquinaria', 'Equipos').",
                                        },
                                        "valor_asegurado": {
                                            "type": "NUMBER",
                                            "description": "Valor monetario asegurado correspondiente al interés.",
                                        },
                                    },
                                    "required": [
                                        "interes_asegurado",
                                        "valor_asegurado",
                                    ],
                                },
                            },
                        },
                        "required": ["ubicacion", "detalle_cobertura"],
                    },
                },
            },
            "required": [
                "detalle_cobertura",
                "total_valores_asegurados",
                "amparos",
                "riesgos",
            ],
        },
    },
    {
        "prompt": """
        Analiza el documento y extrae los siguientes datos:  
        - Prima sin IVA  
        - Monto del IVA  
        - Prima final con IVA  
        - Amparos incluidos, con su deducible correspondiente  

        Devuelve únicamente los campos `prima_sin_iva`, `iva`, `prima_con_iva` y `amparos` en el formato solicitado. No incluyas explicaciones adicionales ni cálculos que no estén en el documento.
""",
        "data": {
            "type": "OBJECT",
            "properties": {
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
                "amparos": {
                    "type": "ARRAY",
                    "description": "Listado de amparos incluidos en la póliza, con su límite por vigencia.",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "amparo": {
                                "type": "STRING",
                                "description": "Nombre del amparo o interés a cubrir.",
                            },
                            "deducible": {
                                "type": "STRING",
                                "description": "Porcentaje o valor mínimo que debe asumir el asegurado en caso de una pérdida o siniestro cubierto antes de que la aseguradora realice el pago correspondiente. Generalmente expresado como un porcentaje del valor de la pérdida con un monto mínimo en SMLMV.",
                            },
                        },
                        "required": ["amparo", "deducible"],
                    },
                },
            },
            "required": ["prima_sin_iva", "iva", "prima_con_iva", "amparos"],
        },
    },
]
