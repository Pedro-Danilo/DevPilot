# POST-H-013-D — Firma y cifrado local opcional

Estado: `implemented-initial`

## Resultado

Se implementa una capa de crypto local opcional para audit packs v2 sin convertirla en dependencia obligatoria. El flujo base `build-v2` y `verify-v2` continúa funcionando sin claves ni backend de cifrado.

## Capacidades

- Firma local opcional con HMAC-SHA256 usando keyfile externo al repo o passphrase desde variable de entorno.
- Cifrado local opcional con Fernet cuando `cryptography` está disponible.
- Fallback explícito sin crypto cuando el modo es `optional` y no hay key/backend.
- BLOCK cuando `sign` o `encrypt` son `required` y falta key/backend.
- BLOCK si el keyfile está dentro del repositorio.
- Verificación opcional de sidecars: firma y encrypted pack.

## Seguridad

```text
network_used=false
external_api_used=false
remote_kms_used=false
keys_in_repo_used=false
compliance_certification_claimed=false
```

La firma/cifrado se ejecutan después del build, redaction y policy checks. Por tanto, no ocultan secretos, errores de redacción ni fallos de integridad.

## Límites

Esta versión no implementa PKI enterprise, certificados X.509, hardware tokens, KMS cloud, rotación avanzada de claves, custodia multiusuario ni declaración de cumplimiento certificado. Es una primera versión local opcional para proteger evidencias en reposo y verificar autenticidad local en entornos controlados.
