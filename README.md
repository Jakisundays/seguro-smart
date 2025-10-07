# Checklist de Debug - Reporte de Riesgos

## 2️⃣ Lectura doble de documentos
**Problema:** Al usar “documentos adicionales en conjunto”, se están leyendo documentos repetidos (ej.: AXA aparece en ambos conjuntos).  

**Pasos a revisar:**
- [ ] Revisar la función que itera sobre los documentos, asegurando que solo lea los documentos del conjunto actual.
- [ ] Confirmar que cada conjunto tenga un identificador único.
- [ ] Verificar que la función de lectura no esté apuntando a la misma lista.
- [ ] Agregar logs para validar qué documentos se leen en cada conjunto.

---

## 4️⃣ Modificar orden de hojas
**Nuevo orden de hojas:**  
1. Riesgo  
2. Amparo  
3. Resumen  

**Pasos a revisar:**
- [ ] Localizar el código donde se generan las hojas del reporte.
- [ ] Modificar el orden según la lista anterior.
- [ ] Verificar que la generación del PDF/Excel respete este nuevo orden.
