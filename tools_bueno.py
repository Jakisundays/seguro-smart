tools = [
    {
        "prompt": (
            "Extrae los valores asegurables explícitos asociados a cada tipo de bien listado en caso de incendio. "
            "Devuelve el monto tal como aparece en el texto (por ejemplo: '$ 24.876.573.178'). "
            "NO INFIERAS: si algún tipo de bien no tiene un monto claro, no devuelvas ningún valor para ese campo. "
            "Incluye también el valor asegurable relacionado a 'Asistencia' si aparece mencionado en el contexto de incendio."
        ),
        "data": {
            "type": "function",
            "function": {
                "name": "valores_asegurables_incendio",
                "description": "Extrae los valores asegurables explícitos por tipo de bien en caso de incendio, si están indicados.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "edificios": {
                            "type": "string",
                            "description": "Valor asegurable de Edificios en caso de incendio, si está indicado.",
                            "nullable": True,
                        },
                        "muebles_y_enseres": {
                            "type": "string",
                            "description": "Valor asegurable de Muebles y Enseres en caso de incendio, si está indicado.",
                            "nullable": True,
                        },
                        "equipos_electricos_y_electronicos": {
                            "type": "string",
                            "description": "Valor asegurable de Equipos Eléctricos y Electrónicos en caso de incendio, si está indicado.",
                            "nullable": True,
                        },
                        "equipo_movil_y_portatil": {
                            "type": "string",
                            "description": "Valor asegurable de Equipo Eléctrico y Electrónico Móvil y Portátil en caso de incendio, si está indicado.",
                            "nullable": True,
                        },
                        "maquinaria_y_equipo": {
                            "type": "string",
                            "description": "Valor asegurable de Maquinaria y Equipo en caso de incendio, si está indicado.",
                            "nullable": True,
                        },
                        "mercancias_fijas": {
                            "type": "string",
                            "description": "Valor asegurable de Mercancías Fijas en caso de incendio, si está indicado.",
                            "nullable": True,
                        },
                        "dineros": {
                            "type": "string",
                            "description": "Valor asegurable de Dineros en caso de incendio, si está indicado.",
                            "nullable": True,
                        },
                        "obras_de_arte": {
                            "type": "string",
                            "description": "Valor asegurable de Obras de Arte en caso de incendio, si está indicado.",
                            "nullable": True,
                        },
                        "asistencia": {
                            "type": "string",
                            "description": "Valor asegurable correspondiente a Asistencia en caso de incendio, si está indicado.",
                            "nullable": True,
                        },
                        "total_valor_asegurable": {
                            "type": "string",
                            "description": "Valor total asegurable indicado en el texto.",
                            "nullable": True,
                        },
                        "tasa_danos_materiales": {
                            "type": "string",
                            "description": "TASA de DAÑOS MATERIALES indicada en el texto. Si no está presente, indicar explícitamente que no se encuentra.",
                            "nullable": True,
                        },
                        "prima": {
                            "type": "string",
                            "description": "PRIMA TOTAL indicada en el texto. Si no está presente, indicar explícitamente que no se encuentra.",
                            "nullable": True,
                        },
                        "limite_por_despacho": {
                            "type": "string",
                            "description": "LÍMITE POR DESPACHO indicado en el contexto de TRANSPORTE DE VALORES. Si no está presente en el texto, indicar explícitamente que no se encuentra.",
                            "nullable": True,
                        },
                        "presupuesto": {
                            "type": "string",
                            "description": "PRESUPUESTO indicado en el contexto de TRANSPORTE DE VALORES. Si no está presente en el texto, indicar explícitamente que no se encuentra.",
                            "nullable": True,
                        },
                    },
                    "required": [
                        "edificios",
                        "muebles_y_enseres",
                        "equipos_electricos_y_electronicos",
                        "equipo_movil_y_portatil",
                        "maquinaria_y_equipo",
                        "mercancias_fijas",
                        "dineros",
                        "obras_de_arte",
                        "total_valor_asegurable",
                        "tasa_danos_materiales",
                        "prima",
                        "limite_por_despacho",
                        "presupuesto",
                    ],
                    "additionalProperties": False,
                },
            },
        },
    },
    {
        "prompt": (
            "Extrae todas las condiciones, coberturas y observaciones explícitas relacionadas con:\n\n"
            "1. **Sustracción en general**: incluyendo porcentajes de cobertura, ubicación de los bienes (ej. dinero en caja fuerte), límites por evento, requisitos de seguridad, etc.\n\n"
            "2. **Sustracción y observaciones para EQUIPO ELECTRÓNICO**: cualquier cobertura especial, condiciones, restricciones, valores o notas específicas que apliquen únicamente al equipo electrónico.\n\n"
            "3. **Observaciones para ROTURA DE MAQUINARIA**: cualquier comentario, excepción, nota o condición relacionada específicamente con rotura de maquinaria.\n\n"
            "Devuelve solo lo que esté claramente indicado en el texto. Si no se encuentra información para alguno de los puntos, indícalo explícitamente."
        ),
        "data": {
            "type": "function",
            "function": {
                "name": "condiciones_sustraccion_y_observaciones",
                "description": (
                    "Extrae las condiciones generales de sustracción, condiciones específicas para equipo electrónico, "
                    "y observaciones relacionadas con rotura de maquinaria, tal como aparecen explícitamente en el texto."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "condiciones_sustraccion": {
                            "type": "array",
                            "description": (
                                "Lista de condiciones y coberturas explícitas relacionadas con sustracción en general. "
                                "Incluye información sobre porcentajes, ubicación del bien, requisitos de seguridad, etc. "
                                "Si no hay información, indicar: 'No se encuentra información explícita sobre sustracción en general.'"
                            ),
                            "items": {"type": "string"},
                            "nullable": True,
                        },
                        "condiciones_equipo_electronico": {
                            "type": "array",
                            "description": (
                                "Condiciones específicas, coberturas u observaciones relacionadas con EQUIPO ELECTRÓNICO. "
                                "Incluye cualquier mención explícita sobre cobertura, exclusión o condición particular. "
                                "Si no hay información, indicar: 'No se encuentra información específica sobre equipo electrónico.'"
                            ),
                            "items": {"type": "string"},
                            "nullable": True,
                        },
                        "observaciones_rotura_maquinaria": {
                            "type": "array",
                            "description": (
                                "Observaciones o condiciones explícitas relacionadas con ROTURA DE MAQUINARIA. "
                                "Incluye excepciones, notas, comentarios relevantes. "
                                "Si no hay información, indicar: 'No se encuentra información específica sobre rotura de maquinaria.'"
                            ),
                            "items": {"type": "string"},
                            "nullable": True,
                        },
                    },
                    "required": [
                        "condiciones_sustraccion",
                        "condiciones_equipo_electronico",
                        "observaciones_rotura_maquinaria",
                    ],
                    "additionalProperties": False,
                },
            },
        },
    },
]
