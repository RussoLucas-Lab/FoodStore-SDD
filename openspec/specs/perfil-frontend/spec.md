# perfil-frontend Specification

## Purpose
Authenticated user profile feature — view and edit personal data (name, surname) and change password with current password verification.

## ADDED Requirements

### Requirement: PerfilForm — ver y editar datos personales
El sistema SHALL renderizar un componente `PerfilForm` en la ruta protegida `/perfil` que muestre el nombre y apellido del usuario logueado y permita editarlos.

#### Scenario: Carga del perfil
- **WHEN** el usuario navega a `/perfil`
- **THEN** los campos `nombre` y `apellido` se pre-populan con los datos actuales del usuario (desde `GET /api/v1/usuarios/me`)

#### Scenario: Edición exitosa
- **WHEN** el usuario modifica nombre o apellido y envía el formulario
- **THEN** se llama `PUT /api/v1/usuarios/me` con los datos nuevos, se muestra un toast de éxito y el `authStore` se actualiza con los datos nuevos

#### Scenario: Error de validación
- **WHEN** el usuario envía el formulario con campos vacíos
- **THEN** TanStack Form muestra mensajes de error por campo sin llamar al API

### Requirement: CambiarPasswordForm — cambio de contraseña
El sistema SHALL renderizar un componente `CambiarPasswordForm` dentro de la página de perfil que permita al usuario cambiar su contraseña proporcionando la contraseña actual.

#### Scenario: Cambio exitoso
- **WHEN** el usuario ingresa la contraseña actual correcta y una nueva contraseña válida (≥ 8 caracteres) confirmada
- **THEN** se llama `PATCH /api/v1/usuarios/me/password`, se muestra un toast de éxito y los campos se limpian

#### Scenario: Contraseña actual incorrecta
- **WHEN** la contraseña actual no coincide con la almacenada
- **THEN** se muestra el error del API como mensaje bajo el campo de contraseña actual

#### Scenario: Confirmación no coincide
- **WHEN** los campos nueva contraseña y confirmación no coinciden
- **THEN** TanStack Form muestra error "Las contraseñas no coinciden" sin llamar al API

#### Scenario: Nueva contraseña débil
- **WHEN** la nueva contraseña tiene menos de 8 caracteres
- **THEN** TanStack Form muestra error de validación sin llamar al API
