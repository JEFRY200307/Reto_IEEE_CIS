# ADR-16: Acceso por SSM con rol IAM; sin SSH abierto ni claves en la instancia

**Estado:** Aceptada · **Fecha:** 2026-10-29 · **Área:** Infraestructura · **Relacionado:** RNF-SE-03, [SPEC-031](../spec/SPEC-031-ejecucion-remota-aws.md)

## Contexto
Una instancia GPU expuesta con SSH abierto o con claves de acceso copiadas dentro es un riesgo: si alguien la compromete, puede generar costos altos (por ejemplo, minería) en la cuenta del equipo.

## Decisión
1. **Nunca usar el usuario raíz** de la cuenta para trabajar. Cada miembro tiene su propio usuario (IAM Identity Center o IAM) con MFA.
2. **Acceso a la instancia con AWS Systems Manager Session Manager** (`aws ssm start-session`). El *security group* no tiene ninguna regla de entrada.
3. La instancia usa un **rol IAM (instance profile)** con solo dos permisos:
   - `AmazonSSMManagedInstanceCore` (para Session Manager).
   - Lectura y escritura **solo** en el bucket del proyecto.
4. No se guardan claves de AWS, tokens de Hugging Face ni otros secretos en el repositorio, en la AMI ni en el *user data*.
5. Plan alternativo si Session Manager no funciona: SSH con un par de claves y una regla de entrada limitada a la IP propia (`/32`), que se borra al terminar.

## Alternativas consideradas
| Alternativa | Por qué no |
|---|---|
| SSH abierto a `0.0.0.0/0` | Expuesto a escaneos automáticos |
| Claves de acceso de AWS dentro de la instancia | Si se filtran, dan acceso a toda la cuenta |
| Usuario raíz | Sin límite de permisos; no recomendado por AWS |

## Consecuencias
- Positivas: sin puertos abiertos; permisos mínimos; nada que filtrar.
- Negativas: hay que instalar el *Session Manager plugin* de AWS CLI en la laptop.
- Verificación: el security group no tiene reglas de entrada; el rol no tiene políticas fuera de las dos indicadas.
