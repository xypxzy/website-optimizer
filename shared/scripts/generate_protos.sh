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

# Директория с .proto файлами (абсолютный путь)
PROTO_DIR="$ROOT_DIR/shared/proto"

# Сервисы, где будут сгенерированы файлы (абсолютные пути)
SERVICES=(
  "$ROOT_DIR/gateway"
  "$ROOT_DIR/parser_service"
  "$ROOT_DIR/analyzer_service"
)

# Функция для генерации .proto файлов
generate_protos() {
  local service_path=$1
  local service_proto_dir="$service_path/proto"
  
  # Проверка существования папки с proto файлами
  if [ ! -d "$service_proto_dir" ]; then
    echo -e "${RED}[$service_path] Директория с .proto файлами не найдена: $service_proto_dir${NC}"
    return 1
  fi

  # Создание директории для сгенерированных файлов, если её нет
  mkdir -p $service_proto_dir

  # Генерация всех .proto файлов из общей директории shared/proto
  for proto_file in $(find $PROTO_DIR -name "*.proto"); do
    echo -e "${GREEN}[$service_path] Генерация файла: $proto_file${NC}"
    python -m grpc_tools.protoc \
      --proto_path=$PROTO_DIR \
      --python_out=$service_proto_dir \
      --grpc_python_out=$service_proto_dir \
      $proto_file
  done
}

# Основной процесс генерации
echo -e "${GREEN}Начало генерации .proto файлов для всех сервисов...${NC}"

for service_path in "${SERVICES[@]}"; do
  echo -e "${GREEN}Генерация .proto файлов для сервиса: $service_path${NC}"
  generate_protos $service_path
done

echo -e "${GREEN}Генерация .proto файлов завершена успешно!${NC}"
