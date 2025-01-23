#!/bin/bash

# Ensure OpenAPI Generator is installed
if ! command -v openapi-generator-cli &> /dev/null; then
    echo "OpenAPI Generator CLI is not installed. Please install it and try again."
    exit 1
fi

# Ensure yq is installed for YAML processing
if ! command -v yq &> /dev/null; then
    echo "yq is not installed. Please install it (https://github.com/mikefarah/yq) and try again."
    exit 1
fi

# Create a temporary file to store the OpenAPI YAML
TEMP_OPENAPI_FILE=$(mktemp --suffix=".yaml")

# Download the OpenAPI YAML
echo "Downloading OpenAPI specification..."
curl -sSL "https://raw.githubusercontent.com/openai/openai-openapi/refs/heads/master/openapi.yaml" -o "$TEMP_OPENAPI_FILE"

if [ $? -ne 0 ]; then
    echo "Failed to download the OpenAPI specification."
    exit 1
fi

echo "OpenAPI specification downloaded to $TEMP_OPENAPI_FILE"

# Filter to keep only the chat completion API
echo "Filtering OpenAPI specification for the chat completion API..."
FILTERED_OPENAPI_FILE=$(mktemp --suffix=".yaml")
yq eval 'del(.paths | with_entries(select(.key != "/v1/chat/completions")))' "$TEMP_OPENAPI_FILE" > "$FILTERED_OPENAPI_FILE"

if [ $? -ne 0 ]; then
    echo "Failed to filter the OpenAPI specification."
    exit 1
fi

echo "Filtered OpenAPI specification saved to $FILTERED_OPENAPI_FILE"

# Create a temporary directory for the generated FastAPI server
TEMP_FASTAPI_DIR=$(mktemp -d)

# Generate the FastAPI server stub
echo "Generating FastAPI server stub for the chat completion API..."
openapi-generator-cli generate \
    -i "$FILTERED_OPENAPI_FILE" \
    -g python-fastapi \
    -o "$TEMP_FASTAPI_DIR"

if [ $? -ne 0 ]; then
    echo "Failed to generate the FastAPI server stub."
    exit 1
fi

# Inform the user about the generated FastAPI code location
echo "FastAPI server stub generated in: $TEMP_FASTAPI_DIR"

# Clean up the temporary OpenAPI files
rm "$TEMP_OPENAPI_FILE" "$FILTERED_OPENAPI_FILE"

# Optionally keep the script running to prevent immediate cleanup
echo "To explore the generated FastAPI project, navigate to:"
echo "cd $TEMP_FASTAPI_DIR"
echo "You will want to update aider/api.py with any differences from this file"

