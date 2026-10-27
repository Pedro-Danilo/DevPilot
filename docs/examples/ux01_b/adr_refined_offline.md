# ADR-001 — Tecnología para ventas locales
## Contexto
RF-002 requiere persistir venta y existencias para una sola propietaria.
## Decisión
El Owner elige T1 Python con SQLite para el MVP local y su carga actual.
## Alternativas
T2 se descarta por operación de servidor adicional sin beneficio comprobado.
## Consecuencias
Positivo: mantenimiento menor. Consecuencia negativa: límites al crecer
la concurrencia, que requiere una migración planificada.
## Riesgos y mitigaciones
RF-002: verificar rollback de venta y stock ante fallo de persistencia; probar restauración en un entorno aislado. Frecuencia y objetivos de recuperación: UNKNOWN, pendientes del Owner.
## Reversibilidad
Revisar al superar la concurrencia prevista y comprobar costos de migración.
