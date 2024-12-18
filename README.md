# Website Optimizer

This project is a backend service for optimizing websites. It includes services for analyzing text content and parsing web pages.

## Services

- **Analyzer Service**: Analyzes text content and provides recommendations for improvement.
- **Parser Service**: Parses web pages to extract headers, CTA buttons, meta tags, and text content.

## Setup

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/website-optimizer.git
   cd website-optimizer
   ```

2. **Create a virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Generate protobuf files**:
   ```bash
   bash shared/scripts/generate_protos.sh
   ```

## Running the Services

### Analyzer Service

1. **Navigate to the analyzer service directory**:

   ```bash
   cd analyzer_service
   ```

2. **Run the service**:
   ```bash
   python app/main.py
   ```

### Parser Service

1. **Navigate to the parser service directory**:

   ```bash
   cd parser_service
   ```

2. **Run the service**:
   ```bash
   python app/main.py
   ```

## Usage

You can interact with the services using gRPC clients. Refer to the protobuf definitions in the `shared/proto` directory for the available RPC methods and message formats.

## License

This project is licensed under the MIT License.
