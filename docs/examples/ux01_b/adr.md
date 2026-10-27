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
Copias verificadas y transacciones atómicas protegen frente a corrupción.
## Reversibilidad
Revisar al superar la concurrencia prevista y comprobar costos de migración.
