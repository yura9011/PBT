# Validación de Prompts para PromptBase

## Matriz de Validación Rápida

Usar esta matriz antes de enviar cualquier prompt a PromptBase.

---

## Fase 1: Validación de Concepto

| Criterio | ✅ Pasa | ❌ Falla | Acción |
|----------|---------|---------|--------|
| ¿Tiene caso de uso comercial? | Múltiples usuarios lo usarían | Solo yo lo usaría | Cambiar idea |
| ¿Es suficientemente amplio? | ≤3 ideas broad | >3 ideas o ideas niche | Generalizar |
| ¿Es único/valioso? | Difícil de adivinar | Obvio/simple | Añadir valor |
| ¿Existe algo similar? | Diferenciado | Copia/muy similar | Innovar |

### Test de 3 Ideas
```
Descomponer el prompt en ideas:
- Idea 1: _____ (broad/niche?)
- Idea 2: _____ (broad/niche?)
- Idea 3: _____ (broad/niche?)

PASA SI: ≤3 ideas Y todas son "broad"
```

---

## Fase 2: Validación de Template

| Criterio | ✅ Pasa | ❌ Falla | Acción |
|----------|---------|---------|--------|
| ¿Tiene [variables]? | Sí, claras | No tiene | Añadir variables |
| ¿Variables son útiles? | Cambian output significativamente | Cambio mínimo | Mejorar variables |
| ¿Es generalizable? | Funciona con muchos inputs | Solo funciona con pocos | Ampliar alcance |

### Checklist de Variables
```
[ ] Variable principal clara: [_____]
[ ] Variable secundaria (si aplica): [_____]
[ ] Cada variable produce output diferente
[ ] Variables tienen nombres descriptivos
```

---

## Fase 3: Validación de Consistencia

| Criterio | ✅ Pasa | ❌ Falla | Acción |
|----------|---------|---------|--------|
| ¿Estilo consistente? | Mismo estilo siempre | Varía entre runs | Refinar prompt |
| ¿Sujeto variable? | Cambia según input | Siempre igual | Verificar variables |
| ¿Reproducible? | Otros pueden replicar | Solo funciona para mí | Simplificar/documentar |

### Test de Consistencia (hacer 5 generaciones)
```
Gen 1: Estilo _____ | Calidad _____
Gen 2: Estilo _____ | Calidad _____
Gen 3: Estilo _____ | Calidad _____
Gen 4: Estilo _____ | Calidad _____
Gen 5: Estilo _____ | Calidad _____

PASA SI: Estilo consistente en 4/5 generaciones
```

---

## Fase 4: Validación de Ejemplos

| Criterio | ✅ Pasa | ❌ Falla | Acción |
|----------|---------|---------|--------|
| ¿Variedad de sujetos? | 5+ sujetos diferentes | <3 sujetos | Generar más variedad |
| ¿Raw output? | Sin editar | Editado/filtrado | Regenerar sin editar |
| ¿Sin collages? | Imágenes individuales | Collages/grids | Upscale individual |
| ¿Calidad alta? | Profesional | Baja calidad | Regenerar mejores |

### Checklist de Ejemplos
```
[ ] Mínimo 4 ejemplos diferentes
[ ] Cada ejemplo con sujeto distinto
[ ] Sin cropping ni filtros
[ ] Sin texto añadido
[ ] Upscaled (si Midjourney)
[ ] Representan bien el rango del prompt
```

---

## Fase 5: Validación de Test Prompt

| Criterio | ✅ Pasa | ❌ Falla | Acción |
|----------|---------|---------|--------|
| ¿Un solo prompt? | Sí | Múltiples | Dejar solo uno |
| ¿Variables rellenadas? | Sí, con valores | Con instrucciones | Limpiar |
| ¿Produce output similar? | Sí | No | Ajustar prompt |

### Formato Correcto
```
PROMPT TEMPLATE:
[Tu prompt con [VARIABLE1] y [VARIABLE2]]

TEST PROMPT:
[Tu prompt con "valor1" y "valor2"]

❌ INCORRECTO:
"Sustituir [VARIABLE1] por valor1"
```

---

## Fase 6: Validación de Contenido

| Criterio | ✅ Pasa | ❌ Falla |
|----------|---------|---------|
| ¿En inglés? | Sí | Otro idioma |
| ¿Sin errores? | Correcto | Typos/errores |
| ¿SFW? | Apropiado | NSFW |
| ¿Legal? | Sí | Dañino/ilegal |
| ¿Original? | Creación propia | Copiado |
| ¿No AI-generated? | Crafted manualmente | Mass-generated |

---

## Fase 7: Validación de Verification Link (si aplica)

| Criterio | ✅ Pasa | ❌ Falla | Acción |
|----------|---------|---------|--------|
| ¿Link funciona? | Sí en incógnito | 404/error | Corregir link |
| ¿Texto coincide? | Exactamente igual | Diferente | Usar DiffChecker |
| ¿Output coincide? | Mismo resultado | Diferente | Regenerar |
| ¿Misma versión? | Sí | Diferente modelo | Regenerar en versión correcta |
| ¿Mismos inputs? | Sí | Con/sin imagen ref | Alinear inputs |

---

## Fase 8: Validación de Thumbnail

| Criterio | ✅ Pasa | ❌ Falla |
|----------|---------|---------|
| ¿Relacionado? | Representa el prompt | No relacionado |
| ¿Alta calidad? | Nítido, bien compuesto | Pixelado/borroso |
| ¿Sin precios? | Limpio | Con $, ratings |
| ¿Mínimo texto? | Visual primero | Mucho texto |
| ¿SFW? | Apropiado | Inapropiado |

---

## Scorecard Final

```
FASE 1 - Concepto:      [ ] PASA  [ ] FALLA
FASE 2 - Template:      [ ] PASA  [ ] FALLA
FASE 3 - Consistencia:  [ ] PASA  [ ] FALLA
FASE 4 - Ejemplos:      [ ] PASA  [ ] FALLA
FASE 5 - Test Prompt:   [ ] PASA  [ ] FALLA
FASE 6 - Contenido:     [ ] PASA  [ ] FALLA
FASE 7 - Verification:  [ ] PASA  [ ] N/A
FASE 8 - Thumbnail:     [ ] PASA  [ ] FALLA

RESULTADO: ___/8 fases pasadas

≥7 PASA → Listo para enviar
5-6 PASA → Revisar fases fallidas
<5 PASA → Requiere trabajo significativo
```

---

## Troubleshooting Rápido

### Si falla "Too Specific"
```
1. Identificar las ideas del prompt
2. Eliminar ideas niche
3. Convertir específicos en [variables]
4. Regenerar ejemplos variados
```

### Si falla "Inconsistent Style"
```
1. Añadir más descriptores de estilo
2. Especificar técnica/medio
3. Añadir parámetros de calidad
4. Probar 10 generaciones
```

### Si falla "Bad Test Generations"
```
1. Verificar prompt correcto
2. Probar en mismo modelo/versión
3. Usar mismos parámetros
4. Simplificar si es muy complejo
```

### Si falla "Example Outputs Too Similar"
```
1. Listar todas las variables
2. Generar con valores muy diferentes
3. Mostrar rango completo de posibilidades
4. Mínimo 5 sujetos distintos
```
