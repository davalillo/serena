#!/bin/bash
# Script de desarrollo para actualizar MQL4 LSP en Serena
# Usage: ./scripts/dev_update_mql4_lsp.sh

set -e  # Salir si hay errores

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para print con color
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "======================================"
echo "  MQL4 LSP Dev Update Script"
echo "======================================"
echo ""

# 1. Buscar y eliminar procesos mql4-lsp-server
print_info "Paso 1: Buscando procesos mql4-lsp-server en ejecución..."

PIDS=$(pgrep -f "mql4-lsp-server" || true)

if [ -n "$PIDS" ]; then
    print_warn "Encontrados procesos mql4-lsp-server ejecutándose:"
    ps aux | grep "mql4-lsp-server" | grep -v grep || true
    echo ""

    print_info "Terminando procesos..."
    for pid in $PIDS; do
        print_info "Matando proceso PID: $pid"
        kill -9 "$pid" 2>/dev/null || true
    done
    print_info "Procesos terminados"
else
    print_info "No hay procesos mql4-lsp-server ejecutándose"
fi

echo ""

# 2. Eliminar directorio MQL4 LSP de .serena
print_info "Paso 2: Eliminando MQL4 LSP del directorio ~/.serena..."

SERENA_DIR="$HOME/.serena"
MQL4_LSP_DIR="$SERENA_DIR/language_servers/static/Mql4LanguageServer"

if [ -d "$MQL4_LSP_DIR" ]; then
    print_info "Eliminando directorio: $MQL4_LSP_DIR"
    rm -rf "$MQL4_LSP_DIR"
    print_info "Directorio eliminado"
else
    print_info "El directorio no existe, no hay nada que eliminar"
fi

echo ""

# 3. Copiar nueva versión desde el directorio de build
print_info "Paso 3: Copiando nueva versión desde directorio de build..."

SOURCE_DIR="./src/bin/Release/net10.0/publish/linux-x64"
SOURCE_FILE="$SOURCE_DIR/mql4-lsp-server"

if [ ! -d "$SOURCE_DIR" ]; then
    print_error "El directorio de build no existe: $SOURCE_DIR"
    print_error "Asegúrate de haber compilado el proyecto primero"
    exit 1
fi

if [ ! -f "$SOURCE_FILE" ]; then
    print_error "El archivo no existe: $SOURCE_FILE"
    print_error "Asegúrate de haber compilado para linux-x64"
    exit 1
fi

print_info "Archivo fuente encontrado: $SOURCE_FILE"

# Crear directorio destino
print_info "Creando directorio destino..."
mkdir -p "$(dirname "$MQL4_LSP_DIR/mql4-lsp/mql4-lsp-server")"

# Copiar archivo
print_info "Copiando archivo..."
cp "$SOURCE_FILE" "$MQL4_LSP_DIR/mql4-lsp/mql4-lsp-server"

# Hacer ejecutable
chmod +x "$MQL4_LSP_DIR/mql4-lsp/mql4-lsp-server"

# Verificar permisos
print_info "Verificando permisos..."
ls -lh "$MQL4_LSP_DIR/mql4-lsp/mql4-lsp-server"

print_info "Archivo copiado exitosamente"

# 4. Verificar versión
echo ""
print_info "Paso 4: Verificando versión instalada..."
DEST_FILE="$MQL4_LSP_DIR/mql4-lsp/mql4-lsp-server"
if [ -f "$DEST_FILE" ]; then
    print_info "Ejecutando $DEST_FILE --version"
    echo "---"
    "$DEST_FILE" --version
    echo "---"
else
    print_error "Error: No se puede verificar la versión. Archivo no encontrado: $DEST_FILE"
fi

echo ""
echo "======================================"
print_info "¡Actualización completada!"
echo "======================================"
echo ""
print_info "El MQL4 LSP en ~/.serena ha sido actualizado"
print_info "La próxima vez que uses Serena, usará esta versión"
echo ""
