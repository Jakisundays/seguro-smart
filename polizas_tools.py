tools = [
    {
        "prompt": """
Analiza el documento proporcionado y extrae la siguiente información:

Detalle de cobertura: listado de intereses asegurados con su nombre (`interes_asegurado`), valor (`valor_asegurado`) y tipo (`tipo`).

Amparos: por cada amparo identificado, devuelve el nombre (`amparo`), deducible (`deducible`) y tipo (`tipo`).

Riesgos: por cada riesgo identificado, devuelve:
- La dirección completa (`ubicacion`).
- Su `detalle_cobertura` con los intereses asegurados, sus valores y tipos.

Tipos disponibles para `tipo` (aplicable a amparos e intereses asegurados):

- 'Incendio': daños por fuego o explosiones.
- 'Sustracción': robo o hurto de bienes asegurados.
- 'Equipo y Maquinaria': daños a equipos y maquinaria de la empresa.
- 'Transporte de Valores': protección durante traslado de dinero o bienes de alto riesgo.
- 'Manejo de Dinero': pérdidas o errores en la custodia y manejo de dinero.
- 'Responsabilidad Civil': daños ocasionados a terceros por el asegurado.

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
                            "tipo": {
                                "type": "STRING",
                                "description": """
                                Tipo de amparo: categoría del amparo según su cobertura. Opciones disponibles:
                                - 'Incendio': daños por fuego o explosiones.
                                - 'Sustracción': robo o hurto de bienes asegurados.
                                - 'Equipo y Maquinaria': daños a equipos y maquinaria de la empresa.
                                - 'Transporte de Valores': protección durante traslado de dinero o bienes de alto riesgo.
                                - 'Manejo de Dinero': pérdidas o errores en la custodia y manejo de dinero.
                                - 'Responsabilidad Civil': daños ocasionados a terceros por el asegurado.
                                """,
                                "enum": [
                                    "Incendio",
                                    "Sustracción",
                                    "Equipo y Maquinaria",
                                    "Transporte de Valores",
                                    "Manejo de Dinero",
                                    "Responsabilidad Civil",
                                ],
                            },
                        },
                        "required": ["amparo", "deducible", "tipo"],
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
                                        "tipo": {
                                            "type": "STRING",
                                            "description": """
                                            Tipo de interés asegurado dentro del riesgo: categoría que describe la cobertura del interés asegurado. Opciones disponibles:
                                            - 'Incendio': daños al interés asegurado por fuego o explosiones.
                                            - 'Sustracción': robo o hurto del interés asegurado.
                                            - 'Equipo y Maquinaria': daños a equipos o maquinaria incluidos en este riesgo.
                                            - 'Transporte de Valores': protección del interés asegurado durante traslado de dinero o bienes de alto riesgo.
                                            - 'Manejo de Dinero': pérdidas o errores relacionados con la custodia y manejo de dinero de este riesgo.
                                            - 'Responsabilidad Civil': daños ocasionados a terceros por el interés asegurado dentro de este riesgo.
                                            """,
                                            "enum": [
                                                "Incendio",
                                                "Sustracción",
                                                "Equipo y Maquinaria",
                                                "Transporte de Valores",
                                                "Manejo de Dinero",
                                                "Responsabilidad Civil",
                                            ],
                                        },
                                    },
                                    "required": [
                                        "interes_asegurado",
                                        "valor_asegurado",
                                        "tipo",
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
- Prima sin IVA (número)
- Monto del IVA (número)
- Prima final con IVA (número)
- Amparos incluidos, con su deducible y tipo correspondiente

Para cada amparo, asigna un `tipo` según las siguientes definiciones:

- 'Incendio': cobertura de daños causados por fuego, explosiones o elementos relacionados con incendio.
- 'Sustracción': protección contra robo, hurto o sustracción de bienes asegurados.
- 'Equipo y Maquinaria': cobertura de daños a equipos, maquinaria o dispositivos usados en operaciones de la empresa.
- 'Transporte de Valores': protección durante el traslado de dinero, valores o bienes de alto riesgo.
- 'Manejo de Dinero': cobertura relacionada con la custodia o manejo de dinero dentro de la empresa, incluyendo errores o pérdidas.
- 'Responsabilidad Civil': cobertura de daños a terceros por acciones u omisiones de la empresa o asegurado.

Devuelve únicamente los campos `prima_sin_iva`, `iva`, `prima_con_iva` y `amparos` en un JSON que respete el formato:
- `prima_sin_iva`, `iva`, `prima_con_iva` → números
- `amparos` → lista de objetos con `amparo` (string), `deducible` (string), `tipo` (ENUM de los anteriores)

No agregues explicaciones ni contenido adicional fuera del JSON.
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
                            "tipo": {
                                "type": "STRING",
                                "description": """
Tipo de amparo: categoría del amparo según su cobertura. Opciones disponibles:
- 'Incendio': daños por fuego o explosiones.
- 'Sustracción': robo o hurto de bienes asegurados.
- 'Equipo y Maquinaria': daños a equipos y maquinaria de la empresa.
- 'Transporte de Valores': protección durante traslado de dinero o bienes de alto riesgo.
- 'Manejo de Dinero': pérdidas o errores en la custodia y manejo de dinero.
- 'Responsabilidad Civil': daños ocasionados a terceros por el asegurado.
""",
                                "enum": [
                                    "Incendio",
                                    "Sustracción",
                                    "Equipo y Maquinaria",
                                    "Transporte de Valores",
                                    "Manejo de Dinero",
                                    "Responsabilidad Civil",
                                ],
                            },
                        },
                        "required": ["amparo", "deducible", "tipo"],
                    },
                },
            },
            "required": ["prima_sin_iva", "iva", "prima_con_iva", "amparos"],
        },
    },
]
