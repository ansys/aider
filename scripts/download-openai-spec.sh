#!/bin/bash

# Ensure OpenAPI Generator is installed
if ! command -v openapi-generator &> /dev/null; then
    echo "OpenAPI Generator CLI is not installed. Please install it and try again."
    exit 1
fi

# Ensure sed is installed and multi os
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v gsed &> /dev/null; then
        echo "Please install gsed (GNU sed) on macOS: brew install gnu-sed"
        exit 1
    fi
    SED_COMMAND="gsed"
else
    if ! command -v sed &> /dev/null; then
        echo "Please install sed on your system."
        exit 1
    fi
    SED_COMMAND="sed"
fi

# Create temporary files manually for better portability
TEMP_OPENAPI_FILE=$(mktemp).yaml

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

if [ $? -ne 0 ]; then
    echo "Failed to filter the OpenAPI specification."
    exit 1
fi

# Create a temporary directory for the generated FastAPI server
TEMP_FASTAPI_DIR=$(mktemp -d)

# Generate the FastAPI server stub
echo "Generating FastAPI server stub for the chat completion API..."
openapi-generator generate \
    -i "$TEMP_OPENAPI_FILE" \
    -g python-fastapi \
    -o "$TEMP_FASTAPI_DIR" \
    --skip-validate-spec

if [ $? -ne 0 ]; then
    echo "Failed to generate the FastAPI server stub."
    exit 1
fi

# Inform the user about the generated FastAPI code location
echo "FastAPI server stub generated in: $TEMP_FASTAPI_DIR"

# Optionally keep the script running to prevent immediate cleanup
echo "To explore the generated FastAPI project, navigate to:"
echo "cd $TEMP_FASTAPI_DIR"

# Copying these to pyi files so you can compare them to the "modified" files
copy_and_sed() {
    cp $1 $2
    if [[ $? -ne 0 ]]; then
        echo "Error copying file from $1 to $2"
        exit 1
    fi

    # Replace the pattern with sed
    $SED_COMMAND -i "s/openapi_server\./aider.api./g" "$2"
    if [[ $? -ne 0 ]]; then
        echo "Error processing file: $2"
        exit 1
    fi
}
copy_and_sed $TEMP_FASTAPI_DIR/src/openapi_server/security_api.py ./aider/api/security_api.py

# apis
copy_and_sed $TEMP_FASTAPI_DIR/src/openapi_server/apis/assistants_api.py ./aider/api/apis/assistants_api.py
copy_and_sed $TEMP_FASTAPI_DIR/src/openapi_server/apis/assistants_api_base.py ./aider/api/apis/assistants_api_base.py

# Models
# There are so many models its best just to copy them all and forget about it...
SRC_DIR="$TEMP_FASTAPI_DIR/src/openapi_server/models/"
DEST_DIR="./aider/api/models/"
for file in "$SRC_DIR"*.py; do
    copy_and_sed "$file" "$DEST_DIR$(basename $file)"
done

# Some known bugs in the generated files
$SED_COMMAND -i "s/desc,/\"desc\",/g" ./aider/api/apis/assistants_api.py

# Get rid of files we dont need
./scripts/prune_models.py --prune-files aider/api/models/*.py --entry-files aider/api/*.py aider/api/apis/**/*.py aider/api/impl/**/*.py --no-dry-run
