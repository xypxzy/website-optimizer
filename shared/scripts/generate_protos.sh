#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Absolute path to the directory containing this script
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$BASE_DIR/../.." && pwd)"

# Directory with .proto files (absolute path)
PROTO_DIR="$ROOT_DIR/shared/proto"

# Services and their corresponding .proto files (absolute paths)
SERVICES=(
  "$ROOT_DIR/gateway:analyzer.proto parser.proto"
  "$ROOT_DIR/parser_service:parser.proto"
  "$ROOT_DIR/analyzer_service:analyzer.proto"
)

# Function to generate .proto files
generate_protos() {
  local service_path=$1
  shift
  local proto_files=("$@")
  local service_proto_dir="$service_path/proto"
  
  # Check if the proto directory exists
  if [ ! -d "$service_proto_dir" ]; then
    echo -e "${RED}[$service_path] Proto directory not found: $service_proto_dir${NC}"
    return 1
  fi

  # Create the directory for generated files if it doesn't exist
  mkdir -p $service_proto_dir

  # Generate the specified .proto files
  for proto_file in "${proto_files[@]}"; do
    echo -e "${GREEN}[$service_path] Generating file: $proto_file${NC}"
    python -m grpc_tools.protoc \
      --proto_path=$PROTO_DIR \
      --python_out=$service_proto_dir \
      --grpc_python_out=$service_proto_dir \
      $PROTO_DIR/$proto_file
  done
}

# Function to fix import paths in generated files
fix_imports() {
  local service_proto_dir=$1
  for file in $(find $service_proto_dir -name "*_pb2_grpc.py" -o -name "*_pb2.py"); do
    sed -i '' 's/import \([^ ]*\)_pb2 as \([^ ]*\)/import proto.\1_pb2 as \2/' $file
  done
}

# Main generation process
echo -e "${GREEN}Starting .proto file generation for all services...${NC}"

for service in "${SERVICES[@]}"; do
  IFS=':' read -r service_path proto_files <<< "$service"
  IFS=' ' read -r -a proto_files_array <<< "$proto_files"
  echo -e "${GREEN}Generating .proto files for service: $service_path${NC}"
  generate_protos $service_path "${proto_files_array[@]}"
  fix_imports "$service_path/proto"
done

echo -e "${GREEN}.proto file generation completed successfully!${NC}"
