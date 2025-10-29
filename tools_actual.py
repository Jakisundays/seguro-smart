tools = [
    {
        "prompt": """
            Analiza el documento proporcionado y extrae la siguiente información:

            - Prima sin IVA (`prima_sin_iva`): valor numérico de la prima antes de IVA.
            - Tasa (`tasa`): porcentaje aplicado en la póliza.
            - Nombre del asegurado (`asegurado`): nombre completo del asegurado tal como aparece en la póliza o documento oficial.

            - Total de valores asegurados (`total_valores_asegurados`): suma total de todos los valores asegurados listados en el detalle.

            Devuelve únicamente los campos:  
            `prima_sin_iva`, `tasa`, `detalle_cobertura`, `total_valores_asegurados`
            
            - Usa números para primas, IVA y tasa.  
            - Strings para nombres de intereses y ubicaciones.  
            - Listas y objetos según la estructura indicada.  

            No inventes información ni calcules valores que no estén explícitamente presentes en el documento.  
            No agregues explicaciones adicionales fuera del JSON.
            """,
        "data": {
            "type": "OBJECT",
            "properties": {
                "total_valores_asegurados": {
                    "type": "STRING",
                    "description": "Suma total de todos los valores asegurados listados en el detalle.",
                },
                "prima_sin_iva": {
                    "type": "NUMBER",
                    "description": "Valor de la prima sin aplicar IVA.",
                },
                "tasa": {
                    "type": "NUMBER",
                    "description": "Porcentaje de la tasa aplicado en la póliza.",
                },
                "asegurado": {
                    "type": "STRING",
                    "description": "Nombre completo del asegurado tal como aparece en la póliza o documento oficial. Ejemplo: 'Juan Pérez S.A.', 'Compañía XYZ Ltda.', 'María Gómez'.",
                },
            },
            "required": [
                "prima_sin_iva",
                "tasa",
                "asegurado",
                "total_valores_asegurados",
            ],
        },
    },
    {
        "prompt": """
            Analiza el documento y extrae los siguientes datos:

            - Amparos incluidos en la póliza, con su deducible y tipo correspondiente.
            - Solo genera líneas para amparos que tengan información válida.  
            - Si un amparo no tiene datos, o su valor es "no especificado", "no encontrado" o "no aplica", NO LO INCLUYAS EN EL RESULTADO. 
            - Excluye de la categoría 'Incendio' cualquier amparo relacionado con honorarios, gastos de preservación, reproducción de información, demostración de pérdida o extinción del siniestro. 
            - Asigna cada amparo a un `tipo` según estas definiciones:
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
            `prima_sin_iva`, `amparos`, `danos_materiales`, `manejo_global_comercial`, `transporte_valores`, `responsabilidad_civil`

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
                # "amparos": {
                #     "type": "ARRAY",
                #     "description": "Listado de amparos incluidos en la póliza, con su límite por vigencia.",
                #     "items": {
                #         "type": "OBJECT",
                #         "properties": {
                #             "amparo": {
                #                 "type": "STRING",
                #                 "description": "Nombre del amparo o interés a cubrir.",
                #             },
                #             "deducible": {
                #                 "type": "STRING",
                #                 "description": "Porcentaje o valor mínimo que debe asumir el asegurado en caso de una pérdida o siniestro cubierto antes de que la aseguradora realice el pago correspondiente. Generalmente expresado como un porcentaje del valor de la pérdida con un monto mínimo en SMLMV.",
                #             },
                #             "tipo": {
                #                 "type": "ARRAY",
                #                 "description": "Tipos de amparo: categorías del amparo según su cobertura. Opciones disponibles: 'Incendio', 'Sustracción', 'Equipo y Maquinaria', 'Transporte de Valores', 'Manejo de Dinero', 'Responsabilidad Civil'.",
                #                 "items": {
                #                     "type": "STRING",
                #                     "enum": [
                #                         "Incendio",
                #                         "Sustracción",
                #                         "Equipo Electronico",
                #                         "Rotura de Maquinaria",
                #                         "Transporte de Valores",
                #                         "Manejo de Dinero",
                #                         "Responsabilidad Civil",
                #                     ],
                #                 },
                #             },
                #         },
                #         "required": ["amparo", "deducible", "tipo"],
                #     },
                # },
            },
            "required": [
                "danos_materiales",
                "manejo_global_comercial",
                "transporte_valores",
                "responsabilidad_civil",
                # "amparos",
            ],
        },
    },
    {
        "prompt": """
            Analiza el documento y extrae todos los riesgos asegurados, generando un listado en el campo `riesgos`.

            Para cada riesgo, incluye:
            - `ubicacion`: dirección completa tal como aparece en el documento (opcional).
            - `detalle_cobertura`: lista de objetos con:
                * `interes_asegurado`: descripción del interés asegurado (ej. 'Edificio', 'Maquinaria', 'Equipos').
                * `valor_asegurado`: valor monetario asegurado correspondiente al interés.
                * `tipo`: lista de tipos de amparo aplicables. Incluye todos los que correspondan y explica brevemente cada uno:
                    - "Incendio": cubre daños materiales ocasionados por fuego.
                    - "Sustracción": cubre robo o hurto de bienes asegurados.
                    - "Equipo Electronico": cubre equipos electrónicos y tecnológicos.
                    - "Rotura de Maquinaria": cubre fallos o daños de maquinaria.
                    - "Transporte de Valores": cubre dinero y objetos de valor durante transporte.
                    - "Manejo de Dinero": cubre custodia, manipulación y transporte interno de dinero.
                    - "Responsabilidad Civil": cubre daños a terceros derivados de la operación del negocio.

            Importante: si el documento menciona explícitamente alguno de los siguientes intereses asegurados, deben incluirse obligatoriamente en el resultado:
            - Edificio
            - Muebles y enseres
            - Maquinaria y equipo
            - Dineros
            - Equipo electrónico
            - Manejo de Dinero
            - Responsabilidad Civil
            - Transporte de Valores

            Nota: Para todos los intereses asegurados mencionados arriba, el campo `interes_asegurado` debe normalizarse a uno de los valores estándar listados, independientemente de cómo aparezca en el documento. Por ejemplo:
            - "Edificio", aunque el documento diga "Edificios", "edificio principal", etc.
            - "Muebles y enseres", aunque aparezca como "muebles", "enseres", etc.
            - "Maquinaria y equipo", aunque aparezca como "maquinaria" o "equipo".
            - "Dineros", aunque aparezca como "dinero", "fondos", etc.
            - "Equipo electrónico", aunque aparezca como "equipos electrónicos", "equipo electrónico", etc.
            - "Manejo de Dinero", aunque aparezca como "manejo de dinero interno", "custodia de dinero", etc.
            - "Responsabilidad Civil", aunque aparezca como "Responsabilidad Civil Extracontractual", "Responsabilidad Civil Contractual", etc.
            - "Transporte de Valores", aunque aparezca como "transporte de dinero", "valores en tránsito", etc.

            Además, para Responsabilidad Civil, el tipo específico (por ejemplo: Extracontractual, Contractual, Producto, Profesional, etc.) deberá incluirse en el campo `tipo`.

            El resultado debe seguir estrictamente el schema JSON proporcionado.
            """,
        "data": {
            "type": "OBJECT",
            "properties": {
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
            },
            "required": ["riesgos"],
        },
    },
    {
        "prompt": """
        Analiza el siguiente texto de una póliza de seguros y extrae únicamente los **deducibles** de cada amparo o subcobertura, organizándolos en las categorías especificadas.

        Cada categoría representa un tipo de riesgo asegurado (por ejemplo, INCENDIO, MANEJO, RESPONSABILIDAD CIVIL, etc.).  
        Solo incluye los deducibles que se mencionen en el texto. Si un amparo no tiene deducible expresamente indicado, **no incluyas ningún valor** para ese campo.

        Sigue estas reglas:
        1. No inventes deducibles.
        2. Mantén los nombres de los amparos tal como aparecen en el schema.
        3. No incluyas campos vacíos si no hay deducible.
        4. No traduzcas el contenido: conserva los nombres y texto originales.
    """,
        "data": {
            "type": "object",
            "properties": {
                "incendio": {
                    "type": "object",
                    "description": "Solo los deducibles de coberturas relacionadas con pérdidas o daños causados por fuego y eventos asociados.",
                    "properties": {
                        "amparo_basico_incendio_y_o_rayo": {
                            "type": "string",
                            "description": "Deducible del amparo por daños materiales directos por incendio o impacto de rayo.",
                        },
                        "terremoto": {
                            "type": "string",
                            "description": "Deducible del amparo por pérdidas o daños materiales causados por movimientos sísmicos.",
                        },
                        "anti_terrorismo": {
                            "type": "string",
                            "description": "Deducible del amparo por daños materiales derivados de actos terroristas o sabotajes.",
                        },
                        "demas_eventos": {
                            "type": "string",
                            "description": "Deducible de otros eventos cubiertos relacionados con el riesgo de incendio.",
                        },
                    },
                    "required": ["amparo_basico_incendio_y_o_rayo", "terremoto", "anti_terrorismo", "demas_eventos"],
                },
                "sustraccion": {
                    "type": "object",
                    "description": "Solo deducibles frente a pérdidas derivadas de hurto o robo calificado.",
                    "properties": {
                        "hurto_calificado": {
                            "type": "string",
                            "description": "Deducible por pérdidas materiales ocasionadas por hurto con violencia o fuerza.",
                        }
                    },
                    "required": ["hurto_calificado"],
                },
                "equipo_electronico": {
                    "type": "object",
                    "description": "Solo deducibles de daños o pérdidas en equipos electrónicos.",
                    "properties": {
                        "hurto_calificado": {
                            "type": "string",
                            "description": "Deducible por robo violento de equipos electrónicos.",
                        },
                        "terremoto": {
                            "type": "string",
                            "description": "Deducible por daños a equipos electrónicos ocasionados por movimientos sísmicos.",
                        },
                        "variacion_de_voltaje": {
                            "type": "string",
                            "description": "Deducible por daños eléctricos causados por variaciones de voltaje.",
                        },
                        "equipo_movil_y_portatil": {
                            "type": "string",
                            "description": "Deducible específico para equipos electrónicos móviles o portátiles.",
                        },
                    },
                    "required": ["hurto_calificado", "terremoto", "variacion_de_voltaje","equipo_movil_y_portatil"],
                },
                "rotura_de_maquinaria": {
                    "type": "object",
                    "description": "Solo deducibles ante daños internos o fallas mecánicas en maquinaria asegurada.",
                    "properties": {
                        "variaciones_de_voltaje_y_danos_internos": {
                            "type": "string",
                            "description": "Deducible por daños internos o eléctricos debidos a variaciones de voltaje o defectos mecánicos.",
                        }
                    },
                    "required": ["variaciones_de_voltaje_y_danos_internos"],
                },
                "manejo": {
                    "type": "object",
                    "description": "Solo deducibles de pérdidas derivadas de actos deshonestos o fraudulentos por empleados o terceros.",
                    "properties": {
                        "amparo_basico": {
                            "type": "string",
                            "description": "Deducible del amparo básico frente a pérdidas por actos deshonestos de empleados.",
                        },
                        "empleados_no_identificados_de_firmas_especializadas_y_temporales": {
                            "type": "string",
                            "description": "Deducible por pérdidas causadas por empleados de empresas contratadas o temporales.",
                        },
                        "perdidas_por_personal_temporal": {
                            "type": "string",
                            "description": "Deducible por pérdidas causadas por empleados temporales identificados.",
                        },
                    },
                    "required": ["amparo_basico", "empleados_no_identificados_de_firmas_especializadas_y_temporales", "perdidas_por_personal_temporal"],
                },
                "responsabilidad_civil_amparo": {
                    "type": "object",
                    "description": "Solo deducibles de la responsabilidad legal del asegurado por daños a terceros.",
                    "properties": {
                        "basico_y_demas_amparos": {
                            "type": "string",
                            "description": "Deducible de la cobertura general de responsabilidad civil básica.",
                        },
                        "gastos_medicos": {
                            "type": "string",
                            "description": "Deducible por gastos médicos de terceros lesionados en un siniestro.",
                        },
                        "responsabilidad_civil_contratistas_y_subcontratistas": {
                            "type": "string",
                            "description": "Deducible por daños ocasionados por contratistas y subcontratistas durante sus labores.",
                        },
                        "rc_vehiculos_propios_y_no_propios": {
                            "type": "string",
                            "description": "Deducible por responsabilidad civil de vehículos propios o no propios.",
                        },
                        "rc_productos_y_trabajos_terminados": {
                            "type": "string",
                            "description": "Deducible por daños ocasionados por productos o trabajos terminados del asegurado.",
                        },
                        "rc_parqueaderos": {
                            "type": "string",
                            "description": "Deducible por daños o pérdidas a vehículos bajo custodia en parqueaderos.",
                        },
                        "bienes_bajo_cuidado_tenencia_y_control": {
                            "type": "string",
                            "description": "Deducible por daños a bienes de terceros bajo responsabilidad del asegurado.",
                        },
                        "responsabilidad_civil_patronal": {
                            "type": "string",
                            "description": "Deducible por reclamaciones de empleados por accidentes laborales.",
                        },
                    },
                    "required": [
                        "basico_y_demas_amparos",
                        "gastos_medicos",
                        "responsabilidad_civil_contratistas_y_subcontratistas",
                        "rc_vehiculos_propios_y_no_propios",
                        "rc_productos_y_trabajos_terminados",
                        "rc_parqueaderos",
                        "bienes_bajo_cuidado_tenencia_y_control",
                        "responsabilidad_civil_patronal",
                    ],
                },
                "transporte_de_valores": {
                    "type": "object",
                    "description": "Solo deducibles frente a pérdidas de dinero o valores durante su transporte.",
                    "properties": {
                        "para_toda_y_cada_perdida": {
                            "type": "string",
                            "description": "Deducible aplicable a cada pérdida durante el transporte de valores.",
                        }
                    },
                    "required": ["para_toda_y_cada_perdida"],
                },
                # "maquinaria_y_equipo": {
                #     "type": "object",
                #     "description": "Solo deducibles de daños a maquinaria pesada y equipos de construcción.",
                #     "properties": {
                #         "terremoto": {
                #             "type": "string",
                #             "description": "Deducible por daños por sismos a maquinaria de construcción.",
                #         },
                #         "anti_terrorismo": {
                #             "type": "string",
                #             "description": "Deducible por daños causados por actos terroristas.",
                #         },
                #         "hurto_calificado": {
                #             "type": "string",
                #             "description": "Deducible por robo con violencia o fuerza de maquinaria o equipos asegurados.",
                #         },
                #         "demas_eventos": {
                #             "type": "string",
                #             "description": "Deducible de otros riesgos aplicables a maquinaria y equipo de construcción.",
                #         },
                #     },
                #     "required": [
                #         "terremoto",
                #         "anti_terrorismo",
                #         "hurto_calificado",
                #         "demas_eventos",
                #     ],
                # },
            },
            "required": [
                "incendio",
                "sustraccion",
                "equipo_electronico",
                "rotura_de_maquinaria",
                "manejo",
                "responsabilidad_civil_amparo",
                "transporte_de_valores",
                # "maquinaria_y_equipo",
            ],
        },
    },
]
