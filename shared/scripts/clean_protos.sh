#!/bin/bash

# Установка флага на выход при ошибке
set -e

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Абсолютный путь до директории, в которой находится этот скрипт
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$BASE_DIR/../.." && pwd)"

# Сервисы, из которых нужно удалить сгенерированные файлы (абсолютные пути)
SERVICES=(
  "$ROOT_DIR/gateway/proto"
  "$ROOT_DIR/parser_service/proto"
  "$ROOT_DIR/analyzer_service/proto"
)

# Маски файлов для удаления
FILE_PATTERNS=(
  "*_pb2.py"
  "*_pb2_grpc.py"
  "*.pyc"
  "__pycache__"
)

# Функция для очистки сгенерированных файлов
clean_protos() {
  local proto_dir=$1
  
  if [ ! -d "$proto_dir" ]; then
    echo -e "${RED}[$proto_dir] Директория не найдена, пропускаем...${NC}"
    return 1
  fi

  echo -e "${GREEN}Очистка файлов в: $proto_dir${NC}"

  for pattern in "${FILE_PATTERNS[@]}"; do
    # Удаляем файлы по шаблону
    find "$proto_dir" -type f -name "$pattern" -exec rm -f {} \;
  done

  # Удаляем __pycache__ директорию, если она есть
  find "$proto_dir" -type d -name "__pycache__" -exec rm -rf {} \;

  echo -e "${GREEN}Очистка завершена для: $proto_dir${NC}"
}

# Основной процесс очистки
echo -e "${GREEN}Начало очистки всех сгенерированных .proto файлов для всех сервисов...${NC}"

for proto_dir in "${SERVICES[@]}"; do
  clean_protos $proto_dir
done

echo -e "${GREEN}Очистка всех сгенерированных .proto файлов завершена успешно!${NC}"
