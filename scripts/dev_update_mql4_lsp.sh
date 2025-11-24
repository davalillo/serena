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

# 3. Obtener MQL4 LSP (local o desde GitHub)
print_info "Paso 3: Obteniendo MQL4 LSP..."

SOURCE_DIR="/home/guillermo/source/mql4-language-server/home/guillermo/source/mql4-language-server"
SOURCE_FILE="$SOURCE_DIR/mql4-lsp-server"
DOWNLOAD_NEEDED=false

# Intentar usar archivo local compilado
if [ -d "$SOURCE_DIR" ] && [ -f "$SOURCE_FILE" ]; then
    print_info "Archivo local encontrado: $SOURCE_FILE"
    print_info "Usando build local..."
else
    print_warn "No se encontró build local en: $SOURCE_DIR"
    echo ""

    # Preguntar si descargar desde GitHub
    read -p "¿Quieres descargar MQL4 LSP v1.3.0 desde GitHub releases? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        DOWNLOAD_NEEDED=true
        print_info "Descargando MQL4 LSP desde GitHub..."
    else
        print_error "Descarga cancelada por el usuario"
        print_error "Para compilar localmente:"
        print_error "  cd src/mql4-lsp-server"
        print_error "  dotnet build -c Release -r linux-x64"
        print_error "  dotnet publish -c Release -r linux-x64 --self-contained false"
        exit 1
    fi
fi

# Crear directorio destino
print_info "Creando directorio destino..."
mkdir -p "$(dirname "$MQL4_LSP_DIR/mql4-lsp/mql4-lsp-server")"

# Si necesita descargar, hacerlo
if [ "$DOWNLOAD_NEEDED" = true ]; then
    # Detectar plataforma
    PLATFORM=$(uname -s)
    ARCH=$(uname -m)

    # Determinar URL según plataforma
    case "$PLATFORM" in
        Linux)
            if [ "$ARCH" = "x86_64" ]; then
                DOWNLOAD_URL="https://github.com/davalillo/mql4-language-server/releases/download/v1.3.0/mql4-lsp-server-linux-x64"
                BINARY_NAME="mql4-lsp-server"
            elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
                print_error "Plataforma Linux ARM64 no soportada en v1.3.0"
                print_error "Compila localmente o usa Linux x64"
                exit 1
            else
                print_error "Arquitectura $ARCH no soportada"
                exit 1
            fi
            ;;
        Darwin)
            if [ "$ARCH" = "x86_64" ]; then
                DOWNLOAD_URL="https://github.com/davalillo/mql4-language-server/releases/download/v1.3.0/mql4-lsp-server-osx-x64"
                BINARY_NAME="mql4-lsp-server"
            elif [ "$ARCH" = "arm64" ]; then
                DOWNLOAD_URL="https://github.com/davalillo/mql4-language-server/releases/download/v1.3.0/mql4-lsp-server-osx-arm64"
                BINARY_NAME="mql4-lsp-server"
            else
                print_error "Arquitectura macOS $ARCH no soportada"
                exit 1
            fi
            ;;
        CYGWIN*|MINGW*|MSYS*)
            DOWNLOAD_URL="https://github.com/davalillo/mql4-language-server/releases/download/v1.3.0/mql4-lsp-server-win-x64.exe"
            BINARY_NAME="mql4-lsp-server.exe"
            ;;
        *)
            print_error "Plataforma $PLATFORM no soportada"
            exit 1
            ;;
    esac

    # Crear directorio temporal
    TEMP_DIR=$(mktemp -d)
    print_info "Descargando en directorio temporal: $TEMP_DIR"

    # Descargar archivo
    if command -v curl &> /dev/null; then
        print_info "Descargando desde: $DOWNLOAD_URL"
        curl -L -o "$TEMP_DIR/$BINARY_NAME" "$DOWNLOAD_URL"
    elif command -v wget &> /dev/null; then
        print_info "Descargando desde: $DOWNLOAD_URL"
        wget -O "$TEMP_DIR/$BINARY_NAME" "$DOWNLOAD_URL"
    else
        print_error "No se encontró curl ni wget para descargar"
        rm -rf "$TEMP_DIR"
        exit 1
    fi

    # Verificar descarga
    if [ ! -f "$TEMP_DIR/$BINARY_NAME" ]; then
        print_error "Error: La descarga falló"
        rm -rf "$TEMP_DIR"
        exit 1
    fi

    print_info "Descarga completada"
    SOURCE_FILE="$TEMP_DIR/$BINARY_NAME"
fi

# Copiar archivo
print_info "Copiando archivo a ~/.serena..."
cp "$SOURCE_FILE" "$MQL4_LSP_DIR/mql4-lsp/mql4-lsp-server"

# Hacer ejecutable
chmod +x "$MQL4_LSP_DIR/mql4-lsp/mql4-lsp-server"

# Limpiar archivo temporal si se descargó
if [ "$DOWNLOAD_NEEDED" = true ]; then
    rm -rf "$TEMP_DIR"
fi

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
