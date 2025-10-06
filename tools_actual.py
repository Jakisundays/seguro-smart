tools = [
    {
        "prompt": """
            Analiza el documento proporcionado y extrae la siguiente información:

            - Prima sin IVA (`prima_sin_iva`): valor numérico de la prima antes de IVA.
            - Monto del IVA (`iva`): valor numérico correspondiente al IVA.
            - Prima final con IVA (`prima_con_iva`): valor numérico de la prima incluyendo IVA.
            - Tasa (`tasa`): porcentaje aplicado en la póliza.

            - Detalle de cobertura (`detalle_cobertura`): listado de intereses asegurados con:
                - Nombre (`interes_asegurado`)
                - Valor asegurado (`valor_asegurado`)
                - Tipo (`tipo`) según las siguientes opciones:
                    - 'Incendio': daños por fuego o explosiones.
                    - 'Sustracción': robo o hurto de bienes asegurados.
                    - 'Equipo Electrónico': daños a equipos electrónicos.
                    - 'Rotura de Maquinaria': fallas o roturas en maquinaria asegurada.
                    - 'Transporte de Valores': protección durante traslado de dinero o bienes de alto valor.
                    - 'Manejo de Dinero': pérdidas o errores en la custodia y manejo de dinero.
                    - 'Responsabilidad Civil': daños ocasionados a terceros por el asegurado.

            - Total de valores asegurados (`total_valores_asegurados`): suma total de todos los valores asegurados listados en el detalle.

            - Riesgos (`riesgos`): listado de riesgos asegurados, cada uno con:
                - Dirección completa (`ubicacion`), tal como aparece en el documento.
                - Su `detalle_cobertura` correspondiente, con intereses asegurados, valores y tipos.

            Devuelve únicamente los campos:  
            `prima_sin_iva`, `iva`, `prima_con_iva`, `tasa`, `detalle_cobertura`, `total_valores_asegurados`, `riesgos`

            - Usa números para primas, IVA y tasa.  
            - Strings para nombres de intereses y ubicaciones.  
            - Listas y objetos según la estructura indicada.  

            No inventes información ni calcules valores que no estén explícitamente presentes en el documento.  
            No agregues explicaciones adicionales fuera del JSON.
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
                            "tipo": {
                                "type": "ARRAY",
                                "description": "Tipos de cobertura aplicables al interés asegurado. Opciones disponibles: 'Incendio', 'Sustracción', 'Equipo Electronico', 'Rotura de Maquinaria', 'Transporte de Valores', 'Manejo de Dinero', 'Responsabilidad Civil'.",
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
                                },
                            },
                        },
                        "required": ["interes_asegurado", "valor_asegurado", "tipo"],
                    },
                },
                "total_valores_asegurados": {
                    "type": "STRING",
                    "description": "Suma total de todos los valores asegurados listados en el detalle.",
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
                                            "type": "ARRAY",
                                            "description": "Tipos de amparo: categorías del amparo según su cobertura. Opciones disponibles: 'Incendio', 'Sustracción', 'Equipo y Maquinaria', 'Transporte de Valores', 'Manejo de Dinero', 'Responsabilidad Civil'.",
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
                                            },
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
                "tasa": {
                    "type": "NUMBER",
                    "description": "Porcentaje de la tasa aplicado en la póliza.",
                },
            },
            "required": [
                "detalle_cobertura",
                "total_valores_asegurados",
                "riesgos",
                "prima_sin_iva",
                "iva",
                "prima_con_iva",
                "tasa",
            ],
        },
    },
    {
        "prompt": """
            Analiza el documento y extrae los siguientes datos:

            - Amparos incluidos en la póliza, con su deducible y tipo correspondiente. Asigna cada amparo a un `tipo` según estas definiciones:
                - 'Incendio': daños causados por fuego, explosiones o elementos relacionados.
                - 'Sustracción': robo, hurto o sustracción de bienes asegurados.
                - 'Equipo Electrónico': daños a equipos electrónicos de la empresa.
                - 'Rotura de Maquinaria': daños a maquinaria por fallas o roturas.
                - 'Transporte de Valores': protección durante el traslado de dinero, valores o bienes de alto riesgo.
                - 'Manejo de Dinero': custodia o manejo de dinero dentro de la empresa, incluyendo errores o pérdidas.
                - 'Responsabilidad Civil': daños a terceros por acciones u omisiones de la empresa o asegurado.

            Extrae también la información de estas secciones:

            - `danos_materiales`: daños materiales que comprenden coberturas como incendio, explosión, daños por agua, vientos fuertes, granizo, humo, caída de aviones u objetos, choque de vehículos, terremotos, temblores, erupciones volcánicas, terrorismo (HMACC y AMIT), sustracción con violencia y sin violencia, hurto de dineros, daños a equipos electrónicos y maquinaria por variaciones de voltaje. Extrae los valores asegurados máximos correspondientes a cada cobertura.

            - `manejo_global_comercial`: cobertura de manejo global comercial o infidelidad de empleados, que incluye abuso de confianza, falsedad, estafa y hurto. Extrae:
                - `perdidas_maximo_anual`
                - `empleados_no_identificados`
                - `empleados_temporales_firma`

            - `transporte_valores`: cobertura de transporte de valores, que incluye pérdida o daño material, terrorismo, robo o hurto y trayectos múltiples. Extrae:
                - `limite_maximo_despacho` (diferenciar tipos si aplica: mensajero solo, acompañado, con acompañante armado, vehículo blindado)
                - `presupuesto_anual_movilizaciones`

            - `responsabilidad_civil`: cobertura de responsabilidad civil, incluyendo vehículos propios y no propios, gastos por urgencias médicas, contratistas y subcontratistas, parqueaderos, cruzada, productos y patronal. Indica si cada cobertura es otorgada como límite único o valor por evento y vigencia. Extrae:
                - `vehiculos_propios_no_propios`
                - `gastos_urgencias_medicas`
                - `contratistas_subcontratistas`
                - `parqueaderos`
                - `cruzada`
                - `productos`
                - `patronal`

            Devuelve únicamente los campos:  
            `prima_sin_iva`, `iva`, `prima_con_iva`, `amparos`, `danos_materiales`, `manejo_global_comercial`, `transporte_valores`, `responsabilidad_civil`

            - Usa números para primas e IVA.  
            - Strings para amparos y coberturas.  
            - Listas y objetos según la estructura indicada.  

            No inventes datos ni agregues explicaciones adicionales fuera del JSON.
            """,
        "data": {
            "type": "OBJECT",
            "properties": {
                "danos_materiales": {
                    "type": "OBJECT",
                    "description": "Daños Materiales que comprende las siguientes coberturas: Incendio, Explosión, daños por agua, vientos fuertes, granizo, humo, caída de aviones u objetos desprendidos, choque de vehículos, terremotos, temblores, erupciones volcánicas, terrorismo (HMACC y AMIT: huelga, motín, asonada, conmoción civil, actos mal intencionados), sustracción con violencia, sustracción sin violencia, hurto de dineros, daños a equipos electrónicos y maquinaria por variaciones de voltaje.",
                    "properties": {
                        "incendio_maximo": {
                            "type": "STRING",
                            "description": "Valor asegurado máximo en Incendio.",
                        },
                        "terremoto_maximo": {
                            "type": "STRING",
                            "description": "Valor asegurado máximo en Terremoto.",
                        },
                        "terrorismo_maximo": {
                            "type": "STRING",
                            "description": "Valor asegurado máximo en HMACC y AMIT (Terrorismo).",
                        },
                        "sustraccion_maximo": {
                            "type": "STRING",
                            "description": "Valor asegurado máximo en Sustracción.",
                        },
                        "dinero_fuera_caja_fuerte": {
                            "type": "STRING",
                            "description": "Valor asegurado máximo de dinero fuera de caja fuerte.",
                        },
                        "dinero_dentro_caja_fuerte": {
                            "type": "STRING",
                            "description": "Valor asegurado máximo de dinero dentro de caja fuerte.",
                        },
                        "sustraccion_sin_violencia": {
                            "type": "STRING",
                            "description": "Valor asegurado para Sustracción sin violencia.",
                        },
                        "equipo_electronico": {
                            "type": "STRING",
                            "description": "Valor asegurado máximo en Equipo Electrónico.",
                        },
                        "equipos_moviles_portatiles": {
                            "type": "STRING",
                            "description": "Valor asegurado máximo en equipos móviles y portátiles.",
                        },
                        "rotura_maquinaria": {
                            "type": "STRING",
                            "description": "Valor asegurado máximo en Rotura de Maquinaria.",
                        },
                    },
                    "required": [
                        "incendio_maximo",
                        "terremoto_maximo",
                        "terrorismo_maximo",
                        "sustraccion_maximo",
                        "dinero_fuera_caja_fuerte",
                        "dinero_dentro_caja_fuerte",
                        "sustraccion_sin_violencia",
                        "equipo_electronico",
                        "equipos_moviles_portatiles",
                        "rotura_maquinaria",
                    ],
                },
                "manejo_global_comercial": {
                    "type": "OBJECT",
                    "description": "Manejo Global Comercial o Infidelidad de Empleados: comprende las coberturas de abuso de confianza, falsedad, estafa y hurto por parte de los empleados a los bienes de la compañía.",
                    "properties": {
                        "perdidas_maximo_anual": {
                            "type": "STRING",
                            "description": "Valor asegurado máximo de pérdidas contratado por año (amparo básico).",
                        },
                        "empleados_no_identificados": {
                            "type": "STRING",
                            "description": "Valor asegurado para empleados no identificados.",
                        },
                        "empleados_temporales_firma": {
                            "type": "STRING",
                            "description": "Valor asegurado para empleados temporales y de firma especializada.",
                        },
                    },
                    "required": [
                        "perdidas_maximo_anual",
                        "empleados_no_identificados",
                        "empleados_temporales_firma",
                    ],
                },
                "transporte_valores": {
                    "type": "OBJECT",
                    "description": "Transporte de valores: comprende las coberturas de pérdida o daño material, terrorismo, robo o hurto y trayectos múltiples.",
                    "properties": {
                        "limite_maximo_despacho": {
                            "type": "STRING",
                            "description": "Valor del límite máximo por despacho. Revisar si presenta varios tipos como: mensajero solo, mensajero acompañado, mensajero con acompañante armado, vehículo blindado.",
                        },
                        "presupuesto_anual_movilizaciones": {
                            "type": "STRING",
                            "description": "Valor del presupuesto anual de movilizaciones.",
                        },
                    },
                    "required": [
                        "limite_maximo_despacho",
                        "presupuesto_anual_movilizaciones",
                    ],
                },
                "responsabilidad_civil": {
                    "type": "OBJECT",
                    "description": "Responsabilidad Civil: comprende varias coberturas que deben indicar si la cobertura es otorgada como límite único o valor por evento y valor por vigencia.",
                    "properties": {
                        "vehiculos_propios_no_propios": {
                            "type": "STRING",
                            "description": "Responsabilidad Civil vehículos propios y no propios: indica si la cobertura es otorgada como límite único o valor por evento y valor por vigencia.",
                        },
                        "gastos_urgencias_medicas": {
                            "type": "STRING",
                            "description": "Gastos por urgencias médicas de terceros: indica si la cobertura es otorgada como límite único o valor por evento y valor por vigencia.",
                        },
                        "contratistas_subcontratistas": {
                            "type": "STRING",
                            "description": "Responsabilidad Civil de Contratistas y Subcontratistas: indica si la cobertura es otorgada como límite único o valor por evento y valor por vigencia.",
                        },
                        "parqueaderos": {
                            "type": "STRING",
                            "description": "Responsabilidad Civil Parqueaderos: indica si la cobertura es otorgada como límite único o valor por evento y valor por vigencia.",
                        },
                        "cruzada": {
                            "type": "STRING",
                            "description": "Responsabilidad Civil Cruzada: indica si la cobertura es otorgada como límite único o valor por evento y valor por vigencia.",
                        },
                        "productos": {
                            "type": "STRING",
                            "description": "Responsabilidad Civil Productos: indica si la cobertura es otorgada como límite único o valor por evento y valor por vigencia.",
                        },
                        "patronal": {
                            "type": "STRING",
                            "description": "Responsabilidad Civil Patronal: indica si la cobertura es otorgada como límite único o valor por evento y valor por vigencia.",
                        },
                    },
                    "required": [
                        "vehiculos_propios_no_propios",
                        "gastos_urgencias_medicas",
                        "contratistas_subcontratistas",
                        "parqueaderos",
                        "cruzada",
                        "productos",
                        "patronal",
                    ],
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
                                "type": "ARRAY",
                                "description": "Tipos de amparo: categorías del amparo según su cobertura. Opciones disponibles: 'Incendio', 'Sustracción', 'Equipo y Maquinaria', 'Transporte de Valores', 'Manejo de Dinero', 'Responsabilidad Civil'.",
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
                                },
                            },
                        },
                        "required": ["amparo", "deducible", "tipo"],
                    },
                },
            },
            "required": [
                "danos_materiales",
                "manejo_global_comercial",
                "transporte_valores",
                "responsabilidad_civil",
                "amparos",
            ],
        },
    },
]
