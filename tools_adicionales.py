tools = [
    {
        "prompt": """
            Analiza el documento proporcionado y extrae la información relacionada con la prima y los amparos de la póliza. Para cada campo, se deben extraer los valores exactos que aparezcan en el documento, sin inventar datos. Los campos a extraer son:

            - Prima sin IVA (`prima_sin_iva`): valor numérico de la prima antes de aplicar el IVA.
            - Nombre del asegurado (`asegurado`): nombre completo del asegurado tal como aparece en la póliza o documento oficial.
            - Tasa (`tasa`): porcentaje de la tasa aplicado en la póliza, que indica el costo del riesgo asumido por la aseguradora.

            - Amparos incluidos en la póliza, con su deducible y tipo correspondiente.
            - Solo genera líneas para amparos que tengan información válida.  
            - Si un amparo no tiene datos, o su valor es "no especificado", "no encontrado" o "no aplica", **no lo incluyas en el resultado**.  
            - Asigna cada amparo a un `tipo` según estas definiciones:
                - 'Incendio': daños causados por fuego, explosiones o elementos relacionados.
                - 'Sustracción': robo, hurto o sustracción de bienes asegurados.
                - 'Equipo Electrónico': daños a equipos electrónicos de la empresa.
                - 'Rotura de Maquinaria': daños a maquinaria por fallas o roturas.
                - 'Transporte de Valores': protección durante el traslado de dinero, valores o bienes de alto riesgo.
                - 'Manejo de Dinero': custodia o manejo de dinero dentro de la empresa, incluyendo errores o pérdidas.
                - 'Responsabilidad Civil': daños a terceros por acciones u omisiones de la empresa o asegurado.

            No inventes información ni agregues explicaciones adicionales.  
            Devuelve únicamente los campos `prima_sin_iva`, `iva`, `prima_con_iva`, `tasa` y `amparos` en un JSON que respete el formato indicado, usando números para primas e IVA y strings para amparos y deducibles.
            """,
        "data": {
            "type": "OBJECT",
            "properties": {
                "prima_sin_iva": {
                    "type": "NUMBER",
                    "description": "Valor de la prima sin aplicar IVA.",
                },
                "asegurado": {
                    "type": "STRING",
                    "description": "Nombre completo del asegurado tal como aparece en la póliza o documento oficial. Ejemplo: 'Juan Pérez S.A.', 'Compañía XYZ Ltda.', 'María Gómez'.",
                },
                "tasa": {
                    "type": "NUMBER",
                    "description": "Porcentaje de la tasa aplicado en la póliza.",
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
                "prima_sin_iva",
                "asegurado",
                "tasa",
                "amparos",
            ],
        },
    },
    {
        "prompt": """
            Analiza el documento proporcionado y extrae la información de las siguientes secciones de la póliza, detallando cada campo:

            - Daños Materiales (`danos_materiales`): cobertura de daños materiales sobre bienes asegurados. Extrae los valores máximos asegurados para cada tipo de cobertura:
                - `incendio_maximo`: valor asegurado máximo por daños por fuego o explosión.
                - `terremoto_maximo`: valor asegurado máximo por daños causados por terremotos o temblores.
                - `terrorismo_maximo`: valor asegurado máximo por eventos de terrorismo, huelga, motín, asonada, conmoción civil o actos mal intencionados (HMACC y AMIT).
                - `sustraccion_maximo`: valor asegurado máximo por sustracción con violencia.
                - `dinero_fuera_caja_fuerte`: valor asegurado máximo para dinero fuera de caja fuerte.
                - `dinero_dentro_caja_fuerte`: valor asegurado máximo para dinero dentro de caja fuerte.
                - `sustraccion_sin_violencia`: valor asegurado máximo para sustracción sin violencia.
                - `equipo_electronico`: valor asegurado máximo para daños a equipos electrónicos.
                - `equipos_moviles_portatiles`: valor asegurado máximo para equipos móviles y portátiles.
                - `rotura_maquinaria`: valor asegurado máximo por rotura de maquinaria.

            - Manejo Global Comercial (`manejo_global_comercial`): cobertura por infidelidad de empleados o manejo inadecuado de bienes de la empresa. Extrae:
                - `perdidas_maximo_anual`: valor asegurado máximo de pérdidas por año.
                - `empleados_no_identificados`: valor asegurado para pérdidas causadas por empleados no identificados.
                - `empleados_temporales_firma`: valor asegurado para pérdidas causadas por empleados temporales o de firma especializada.

            - Transporte de Valores (`transporte_valores`): cobertura durante el traslado de dinero o bienes de alto valor. Extrae:
                - `limite_maximo_despacho`: valor asegurado máximo por despacho, indicando variantes como mensajero solo, acompañado, con acompañante armado o vehículo blindado si aplica.
                - `presupuesto_anual_movilizaciones`: valor del presupuesto anual destinado a movilizaciones de valores.

            - Responsabilidad Civil (`responsabilidad_civil`): cobertura por daños a terceros ocasionados por la empresa o asegurado. Extrae los valores para cada tipo de cobertura, indicando si se otorga como límite único o valor por evento y vigencia:
                - `vehiculos_propios_no_propios`: cobertura para vehículos propios y no propios.
                - `gastos_urgencias_medicas`: gastos por urgencias médicas de terceros.
                - `contratistas_subcontratistas`: cobertura para contratistas y subcontratistas.
                - `parqueaderos`: cobertura para parqueaderos.
                - `cruzada`: cobertura cruzada entre diferentes áreas o riesgos.
                - `productos`: cobertura relacionada con productos.
                - `patronal`: cobertura patronal que protege al empleador ante daños causados por empleados.

            No inventes información ni agregues explicaciones adicionales.  
            Devuelve únicamente los campos `danos_materiales`, `manejo_global_comercial`, `transporte_valores` y `responsabilidad_civil` en un JSON que respete la estructura indicada.
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
            },
            "required": [
                "danos_materiales",
                "manejo_global_comercial",
                "transporte_valores",
                "responsabilidad_civil",
            ],
        },
    },
]
