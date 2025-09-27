<!-- TODO:
Pedir la tasa y prima del doc actual y renovacion
Pedir la tas de los docs adicionales
Pedir en las tools  "danos_materiales": {
            "incendio_maximo": "$31.432.470.033",
            "terremoto_maximo": "$31.432.470.033",
            "terrorismo_maximo": "$31.432.470.033",
            "sustraccion_maximo": "$4.627.502.059",
            "dinero_fuera_caja_fuerte": "$10.000.000",
            "dinero_dentro_caja_fuerte": "$30.000.000",
            "sustraccion_sin_violencia": "$984.208.430",
            "equipo_electronico": "$1.309.227.904",
            "equipos_moviles_portatiles": "$20.000.000",
            "rotura_maquinaria": "$3.221.334.452",
        },
        "manejo_global_comercial": {
            "perdidas_maximo_anual": "No especificado",
            "empleados_no_identificados": "No especificado",
            "empleados_temporales_firma": "No especificado",
        },
        "transporte_valores": {
            "limite_maximo_despacho": "No especificado",
            "presupuesto_anual_movilizaciones": "No especificado",
        },
        "responsabilidad_civil": {
            "vehiculos_propios_no_propios": "No especificado",
            "gastos_urgencias_medicas": "No especificado",
            "contratistas_subcontratistas": "No especificado",
            "parqueaderos": "No especificado",
            "cruzada": "No especificado",
            "productos": "No especificado",
            "patronal": "No especificado",
        },

        para los doc actual y de renovacion

  esto con lleva arreglar las propiedades y el prompt
  preguntar a Rocio q onda con equipo electronico y Rotura maquinaria?
  cae bajo: "danos_materiales": {
            "incendio_maximo": "$31.432.470.033",
            "terremoto_maximo": "$31.432.470.033",
            "terrorismo_maximo": "$31.432.470.033",
            "sustraccion_maximo": "$4.627.502.059",
            "dinero_fuera_caja_fuerte": "$10.000.000",
            "dinero_dentro_caja_fuerte": "$30.000.000",
            "sustraccion_sin_violencia": "$984.208.430",
            "equipo_electronico": "$1.309.227.904",
            "equipos_moviles_portatiles": "$20.000.000",
            "rotura_maquinaria": "$3.221.334.452",
        } 
        ???

  integrar funcion de crear el exdel output al excel con las otras hojas
  implementar todo 
  testear
  deploy
 -->
````markdown
# TODO - Procesamiento de pólizas

- [ ] Pedir la **tasa y prima**  
  - [ ] Documento actual  
  - [ ] Documento de renovación  

- [ ] Pedir la **tasa** de los **documentos adicionales**

- [ ] Ajustar `tools` en ambos documentos (actual y renovación) con las siguientes secciones:  
  ```json
  "danos_materiales": {
    "incendio_maximo": "$31.432.470.033",
    "terremoto_maximo": "$31.432.470.033",
    "terrorismo_maximo": "$31.432.470.033",
    "sustraccion_maximo": "$4.627.502.059",
    "dinero_fuera_caja_fuerte": "$10.000.000",
    "dinero_dentro_caja_fuerte": "$30.000.000",
    "sustraccion_sin_violencia": "$984.208.430",
    "equipo_electronico": "$1.309.227.904",
    "equipos_moviles_portatiles": "$20.000.000",
    "rotura_maquinaria": "$3.221.334.452"
  },
  "manejo_global_comercial": {
    "perdidas_maximo_anual": "No especificado",
    "empleados_no_identificados": "No especificado",
    "empleados_temporales_firma": "No especificado"
  },
  "transporte_valores": {
    "limite_maximo_despacho": "No especificado",
    "presupuesto_anual_movilizaciones": "No especificado"
  },
  "responsabilidad_civil": {
    "vehiculos_propios_no_propios": "No especificado",
    "gastos_urgencias_medicas": "No especificado",
    "contratistas_subcontratistas": "No especificado",
    "parqueaderos": "No especificado",
    "cruzada": "No especificado",
    "productos": "No especificado",
    "patronal": "No especificado"
  }
````

* [ ] Corregir propiedades y prompt

  * Evitar que invente datos
  * Evitar que calcule totales no presentes
  * Forzar extracción literal en formato claro

* [ ] Confirmar con **Rocío**

  * ¿`equipo_electronico` y `rotura_maquinaria` caen bajo `"danos_materiales"`?
  * Documentar su respuesta

* [ ] Integrar función para exportar el output a **Excel** con todas las hojas necesarias

* [ ] Implementar el flujo completo

  * Extracción → normalización → Excel

* [ ] Testear

  * Unit tests para normalización y mapeo
  * End-to-end con documentos actual, renovación y adicional

* [ ] Deploy

  * Preparar Dockerfile / script
  * Subir a staging
  * Pasar a producción después de validar

```
```



Hay q agregar docs conjuntos a docs adicionales 

arreglar:
"danos_materiales":{...}
"manejo_global_comercial":{...}
"transporte_valores":{...}
"responsabilidad_civil":{...}

en el excel para los docs adicionales y actual y renovacion

agregar prima al excel en docs adicionales

agregar esa hoja de excel a las demas
agregar todo al flujo
probar
deploy