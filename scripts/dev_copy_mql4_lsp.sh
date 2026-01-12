#!/bin/bash
# Script simple de desarrollo para copiar MQL4 LSP a Serena
# Usage: ./scripts/dev_copy_mql4_lsp.sh

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SOURCE_DIR="/home/guillermo/source/mql4-language-server/src/bin/Release/net10.0/publish/linux-x64"
SOURCE_FILE="$SOURCE_DIR/mql4-lsp-server-linux-x64"

DEST_DIR="$HOME/.serena/language_servers/static/Mql4LanguageServer/mql4-lsp"
DEST_DIR2="$HOME/.solidlsp/language_servers/static/Mql4LanguageServer/mql4-lsp"
DEST_FILE="$DEST_DIR/mql4-lsp-server"
DEST_FILE2="$DEST_DIR2/mql4-lsp-server"

echo "======================================"
echo "  Copiar MQL4 LSP a Serena"
echo "======================================"
echo ""

# Verificar archivo fuente
if [ ! -f "$SOURCE_FILE" ]; then
    echo -e "${YELLOW}[WARN]${NC} Archivo fuente no encontrado: $SOURCE_FILE"
    echo "Asegúrate de haber compilado el proyecto para linux-x64"
    exit 1
fi

echo -e "${GREEN}[INFO]${NC} Archivo fuente: $SOURCE_FILE"
ls -lh "$SOURCE_FILE"

# Crear directorio destino
echo -e "${GREEN}[INFO]${NC} Creando directorio destino..."
mkdir -p "$DEST_DIR"

# Borrar archivo destino si existe
if [ -f "$DEST_FILE" ]; then
    echo -e "${YELLOW}[INFO]${NC} Archivo $DEST_FILE  existe, borrándolo..."
    rm -f "$DEST_FILE"
fi

# Borrar archivo destino si existe
if [ -f "$DEST_FILE2" ]; then
    echo -e "${YELLOW}[INFO]${NC} Archivo $DEST_FILE2 existe, borrándolo..."
    rm -f "$DEST_FILE2"
fi

# Copiar archivo
echo -e "${GREEN}[INFO]${NC} Copiando archivo..."
pkill -f mql4-lsp-server 2>/dev/null || true
cp "$SOURCE_FILE" "$DEST_FILE"
cp "$SOURCE_FILE" "$DEST_FILE2"
chmod +x "$DEST_FILE"
chmod +x "$DEST_FILE2"

# Verificar versión
echo ""
echo -e "${GREEN}[INFO]${NC} Verificando versión instalada..."
echo -e "${GREEN}[INFO]${NC} Ejecutando $DEST_FILE --version"
echo "---"
"$DEST_FILE" --version
echo "---"

# Verificar versión
echo ""
echo -e "${GREEN}[INFO]${NC} Verificando versión instalada..."
echo -e "${GREEN}[INFO]${NC} Ejecutando $DEST_FILE2 --version"
echo "---"
"$DEST_FILE2" --version
echo "---"

echo ""
echo -e "${GREEN}[INFO]${NC} ¡Copiado exitosamente!"
echo -e "${GREEN}[INFO]${NC} Destino: $DEST_FILE"
ls -lh "$DEST_FILE"
echo ""

echo ""
echo -e "${GREEN}[INFO]${NC} ¡Copiado exitosamente!"
echo -e "${GREEN}[INFO]${NC} Destino: $DEST_FILE2"
ls -lh "$DEST_FILE2"
echo ""
