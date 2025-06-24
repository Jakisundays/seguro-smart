# TODO List - Proyecto

## 1. Crear `requirements.txt`
- [ ] Revisar todas las dependencias usadas en el proyecto
- [ ] Generar el archivo `requirements.txt` con `pip freeze > requirements.txt`
- [ ] Verificar que el archivo incluya todas las librerías necesarias para deploy

## 2. Hacer deploy
- [ ] Definir el entorno de producción (Droplet, servidor, etc.)
- [ ] Configurar variables de entorno necesarias
- [ ] Crear script o pipeline automatizado para deploy (GitHub Actions, webhook, etc.)
- [ ] Probar deploy manualmente para asegurar que funcione correctamente
- [ ] Documentar el proceso de deploy en el README o en un archivo aparte

## 3. Agregar observaciones a las tools para mostrar información clave
- [ ] Identificar qué observaciones son relevantes para cada tool
- [ ] Para cada key, agregar la observación en el código o data:
  - [ ] `"gastos_medicos_por_accidente"`
  - [ ] `"rehabilitacion_integral_por_accidente"`
  - [ ] `"ambulancia_para_eventos"`
    - [ ] *Nota:* Esta debe manejarse como un array de observaciones (varias entradas)
- [ ] Validar que las observaciones se muestren correctamente en la UI o output

## 4. Mejorar prompts para pedir ayuda (para entender qué pedir y corregir errores)
- [ ] Revisar prompts actuales y detectar fallos o confusiones
- [ ] Definir claramente qué información se necesita para cada caso:
  - [ ] `"plazo_aviso_siniestro"`
  - [ ] `"plazo_pago_siniestro"`
- [ ] Testear nuevos prompts para asegurar que la info recibida sea precisa y útil

## 5. Arreglar UI para comparación y mostrar observaciones con Streamlit
- [ ] Revisar la estructura actual de la UI para la tabla comparativa
- [ ] Modificar clases CSS y componentes para que el diseño sea claro y responsivo
- [ ] Adaptar el output para que las observaciones se muestren bien junto a los datos
- [ ] Testear la UI con diferentes datos para validar que todo se vea y funcione bien

---

> **Notas generales:**  
> - Mantener código limpio y documentado.  
> - Usar control de versiones para cada cambio importante.  
> - Pedir feedback si algún paso no queda claro o si necesitas ayuda puntual.
