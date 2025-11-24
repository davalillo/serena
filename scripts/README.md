# Scripts de Desarrollo

Esta carpeta contiene scripts útiles para el desarrollo de Serena y especialmente para el desarrollo del MQL4 LSP.

## Scripts de MQL4 LSP

### `dev_update_mql4_lsp.sh`

Script completo para desarrollo del MQL4 LSP que:

1. **Busca y elimina procesos mql4-lsp-server** en ejecución (útil para limpiar procesos zombi)
2. **Elimina completamente** el directorio `~/.serena/language_servers/static/Mql4LanguageServer/`
3. **Copia la nueva versión** desde `./src/bin/Release/net10.0/publish/linux-x64/mql4-lsp-server`

**Uso:**
```bash
./scripts/dev_update_mql4_lsp.sh
```

**Cuándo usarlo:**
- Después de hacer cambios significativos en el LSP
- Si hay procesos zombi del LSP anterior
- Para garantizar una instalación completamente limpia

### `dev_copy_mql4_lsp.sh`

Script simple para copiar solo el archivo del LSP:

1. **Copia el binary** desde `./src/bin/Release/net10.0/publish/linux-x64/mql4-lsp-server`
2. **Lo coloca en** `~/.serena/language_servers/static/Mql4LanguageServer/mql4-lsp/`
3. **Mantiene permisos** ejecutables

**Uso:**
```bash
./scripts/dev_copy_mql4_lsp.sh
```

**Cuándo usarlo:**
- Para actualizaciones rápidas durante desarrollo
- Si solo cambió el binary, no la estructura
- Cuando no hay procesos zombi

## Requisitos

### Para desarrollo del MQL4 LSP:

1. **Compilar el MQL4 LSP** primero:
   ```bash
   cd src/mql4-lsp-server
   dotnet build -c Release
   dotnet publish -c Release -r linux-x64 --self-contained false
   ```

2. **Verificar el directorio de salida:**
   ```
   ./src/bin/Release/net10.0/publish/linux-x64/mql4-lsp-server
   ```

### Para ejecutar los scripts:

```bash
# Hacer ejecutables (solo la primera vez)
chmod +x scripts/dev_update_mql4_lsp.sh
chmod +x scripts/dev_copy_mql4_lsp.sh

# Ejecutar
./scripts/dev_update_mql4_lsp.sh
# O
./scripts/dev_copy_mql4_lsp.sh
```

## Estructura de directorios

### Antes de ejecutar el script:
```
~/.serena/language_servers/static/
└── Mql4LanguageServer/
    └── mql4-lsp/
        └── mql4-lsp-server  ← Versión anterior
```

### Después de ejecutar el script:
```
~/.serena/language_servers/static/
└── Mql4LanguageServer/
    └── mql4-lsp/
        └── mql4-lsp-server  ← Versión nueva (actualizada)
```

## Flujo de trabajo recomendado

### Para desarrollo activo del LSP:

```bash
# 1. Hacer cambios en el LSP (en src/mql4-lsp-server/)
# 2. Compilar
dotnet build -c Release -r linux-x64

# 3. Ejecutar el script de actualización
./scripts/dev_update_mql4_lsp.sh

# 4. Probar en Serena
cd /path/to/your/mql4/project
serena  # o el comando que uses
```

### Para desarrollo rápido (solo cambios menores):

```bash
# 1. Hacer cambios pequeños en el LSP
# 2. Compilar
dotnet build -c Release -r linux-x64

# 3. Copiar solo el binary
./scripts/dev_copy_mql4_lsp.sh

# 4. Probar
# (si hay problemas, usar dev_update_mql4_lsp.sh)
```

## Solución de problemas

### Error: "directorio de build no existe"
```bash
# Solución: Compilar primero
cd src/mql4-lsp-server
dotnet build -c Release -r linux-x64
dotnet publish -c Release -r linux-x64 --self-contained false
```

### Error: "permisos denegados"
```bash
# Solución: Hacer ejecutables
chmod +x ~/.serena/language_servers/static/Mql4LanguageServer/mql4-lsp/mql4-lsp-server
```

### Procesos zombi después de cerrar Serena:
```bash
# Usar el script completo que los mata
./scripts/dev_update_mql4_lsp.sh

# O manualmente:
pkill -9 mql4-lsp-server
```

### Verificar qué versión está usando Serena:

```bash
# Ver fecha del archivo
ls -lh ~/.serena/language_servers/static/Mql4LanguageServer/mql4-lsp/mql4-lsp-server

# Comparar con la versión local
ls -lh ./src/bin/Release/net10.0/publish/linux-x64/mql4-lsp-server
```

## Notas

- Los scripts usan rutas relativas, ejecútalos desde la raíz del proyecto
- Los scripts son seguros: verifican que los archivos existen antes de proceder
- El script completo es más lento pero más seguro (elimina todo y recrea)
- El script simple es más rápido pero asume que el directorio ya existe

## Personalización

Si tu directorio de build es diferente, edita la variable `SOURCE_DIR` en los scripts:

```bash
SOURCE_DIR="./src/bin/Release/net10.0/publish/linux-x64"
# Cambiar a tu directorio
SOURCE_DIR="/ruta/a/tu/build/directory"
```
