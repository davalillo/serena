# Scripts de Desarrollo

Esta carpeta contiene scripts útiles para el desarrollo de Serena y especialmente para el desarrollo del MQL4 LSP.

## Scripts de MQL4 LSP

### `dev_update_mql4_lsp.sh`

Script completo para desarrollo del MQL4 LSP que:

1. **Busca y elimina procesos mql4-lsp-server** en ejecución (útil para limpiar procesos zombi)
2. **Elimina completamente** el directorio `~/.serena/language_servers/static/Mql4LanguageServer/`
3. **Obtiene el MQL4 LSP**:
   - **Primero** intenta usar `/home/guillermo/source/mql4-language-server/home/guillermo/source/mql4-language-server/mql4-lsp-server` (build local)
   - **Si no existe** pide confirmación para descargar desde GitHub releases v1.3.0
   - **Descarga automáticamente** según la plataforma (Linux x64, macOS x64/arm64, Windows x64)
4. **Verifica la versión** ejecutando `--version` al final

**Uso:**
```bash
./scripts/dev_update_mql4_lsp.sh
```

**Cuándo usarlo:**
- Después de hacer cambios significativos en el LSP
- Si hay procesos zombi del LSP anterior
- Para garantizar una instalación completamente limpia
- Para instalar LSP sin compilar localmente
- Para verificar qué versión se instaló

**Flujo de trabajo:**
```
1. Script busca build local en /home/guillermo/source/mql4-language-server/home/guillermo/source/mql4-language-server
2. Si no existe, pregunta: "¿Descargar desde GitHub? (y/N)"
3. Si 'y', detecta plataforma y descarga v1.3.0
4. Copia a ~/.serena
5. Verifica versión con --version
```

**Salida esperada (build local):**
```
[INFO] Archivo local encontrado: /home/guillermo/source/mql4-language-server/home/guillermo/source/mql4-language-server/mql4-lsp-server
[INFO] Usando build local...
[INFO] Paso 4: Verificando versión instalada...
---
MQL4 Language Server v1.4.0-dev
---
```

**Salida esperada (descarga desde GitHub):**
```
[WARN] No se encontró build local
¿Quieres descargar MQL4 LSP v1.3.0 desde GitHub releases? (y/N): y
[INFO] Descargando MQL4 LSP desde GitHub...
[INFO] Descargando desde: https://github.com/...
[INFO] Descarga completada
[INFO] Paso 4: Verificando versión instalada...
---
MQL4 Language Server v1.3.0
---
```

### `dev_copy_mql4_lsp.sh`

Script simple para copiar solo el archivo del LSP:

1. **Copia el binary** desde `/home/guillermo/source/mql4-language-server/home/guillermo/source/mql4-language-server/mql4-lsp-server`
2. **Lo coloca en** `~/.serena/language_servers/static/Mql4LanguageServer/mql4-lsp/`
3. **Mantiene permisos** ejecutables
4. **Verifica la versión** ejecutando `./mql4-lsp-server --version` al final

**Uso:**
```bash
./scripts/dev_copy_mql4_lsp.sh
```

**Cuándo usarlo:**
- Para actualizaciones rápidas durante desarrollo
- Si solo cambió el binary, no la estructura
- Cuando no hay procesos zombi
- Para verificar la versión copiada

**Salida esperada:**
```
[INFO] Verificando versión instalada...
[INFO] Ejecutando ~/.serena/language_servers/static/Mql4LanguageServer/mql4-lsp/mql4-lsp-server --version
---
MQL4 Language Server v1.4.0-dev
---
```

## Requisitos

### Para desarrollo del MQL4 LSP:

1. **Compilar el MQL4 LSP** primero:
   ```bash
   cd /home/guillermo/source/mql4-language-server
   dotnet build -c Release
   dotnet publish -c Release -r linux-x64 --self-contained false
   ```

2. **Verificar el directorio de salida:**
   ```
   /home/guillermo/source/mql4-language-server/home/guillermo/source/mql4-language-server/mql4-lsp-server
   ```

### Opción: Descarga desde GitHub

Si no tienes el código fuente del LSP compilado, puedes descargar la versión oficial v1.3.0:

**Plataformas soportadas:**
- Linux x64
- macOS x64 (Intel)
- macOS Arm64 (Apple Silicon)
- Windows x64

**El script `dev_update_mql4_lsp.sh` lo hace automáticamente:**
1. Intenta usar build local
2. Si no existe, pregunta si descargar
3. Descarga automáticamente según tu plataforma
4. Lo instala en `~/.serena/`

**Descarga manual:**
```bash
# Linux x64
curl -L -o mql4-lsp-server https://github.com/davalillo/mql4-language-server/releases/download/v1.3.0/mql4-lsp-server-linux-x64

# macOS x64
curl -L -o mql4-lsp-server https://github.com/davalillo/mql4-language-server/releases/download/v1.3.0/mql4-lsp-server-osx-x64

# macOS Arm64
curl -L -o mql4-lsp-server https://github.com/davalillo/mql4-language-server/releases/download/v1.3.0/mql4-lsp-server-osx-arm64

# Windows x64
curl -L -o mql4-lsp-server.exe https://github.com/davalillo/mql4-language-server/releases/download/v1.3.0/mql4-lsp-server-win-x64.exe
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
ls -lh /home/guillermo/source/mql4-language-server/home/guillermo/source/mql4-language-server/mql4-lsp-server
```

### La verificación de versión falla o no muestra nada:

```bash
# Ejecutar manualmente para ver el error
~/.serena/language_servers/static/Mql4LanguageServer/mql4-lsp/mql4-lsp-server --version

# Si el binary no responde, verificar permisos
chmod +x ~/.serena/language_servers/static/Mql4LanguageServer/mql4-lsp/mql4-lsp-server

# Verificar que es realmente un executable
file ~/.serena/language_servers/static/Mql4LanguageServer/mql4-lsp/mql4-lsp-server
```

## Verificación de versión

Los scripts ejecutan automáticamente `--version` al final para confirmar que se instaló correctamente.

### Interpretar la salida:

**Versión instalada correctamente:**
```
---
MQL4 Language Server v1.4.0-dev
Build: 2024-11-24
---
```

**Si no muestra nada o da error:**
- El binary podría estar corrupto
- Compilar de nuevo con `dotnet clean && dotnet build -c Release -r linux-x64`
- Verificar que el archivo se copió correctamente

**Para versiones sin --version flag:**

Si tu LSP no soporta `--version`, puedes usar:

```bash
# Ver fecha de compilación
stat ~/.serena/language_servers/static/Mql4LanguageServer/mql4-lsp/mql4-lsp-server

# O comprobar hash del archivo
md5sum ~/.serena/language_servers/static/Mql4LanguageServer/mql4-lsp/mql4-lsp-server
md5sum /home/guillermo/source/mql4-language-server/home/guillermo/source/mql4-language-server/mql4-lsp-server
```

Los hashes deben coincidir si se copió correctamente.

## Notas

- Los scripts usan rutas relativas, ejecútalos desde la raíz del proyecto
- Los scripts son seguros: verifican que los archivos existen antes de proceder
- El script completo es más lento pero más seguro (elimina todo y recrea)
- El script simple es más rápido pero asume que el directorio ya existe

## Personalización

Si tu directorio de build es diferente, edita la variable `SOURCE_DIR` en los scripts:

```bash
SOURCE_DIR="/home/guillermo/source/mql4-language-server/home/guillermo/source/mql4-language-server"
# Cambiar a tu directorio
SOURCE_DIR="/ruta/a/tu/build/directory"
```
