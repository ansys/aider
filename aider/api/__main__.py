"""
This is useful as both a fastapi uvicorn server, AND as a library.

The API is OpenAI /v1/chat/completions compatible and works with litellm.

The API is stateful, in that it assumes:

* the server or working directory is located in a git repo
* it has access to read and update history files and make commits

So you DON'T need to pass more than one message to it each interaction.

How it differs from `aider.main:main` however is it is not a live session.
It will send you Y/N questions as responses, then "stops". Then resume when you send an answer back.
whereas `aider.main:main` maintains a live connection in your terminal and "hangs" until you reply.

I will call this distinction "transactional" vs "live"

So this is a "stateful" "transactional" api. Whereas the other is a "stateful" "live" environment.

Run using `uvicorn aider.api:app --reload`
"""

from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from aider.api import *

BRANCH_PREFIX = "aider"

app = FastAPI(
    title="Assistants API",
    description="An OpenAPI-compatible assistant endpoint",
    version="1.0.0",
)


@app.post("v1/assistants/createAssistant")
async def create_assistant() -> None:
    """
    This is going to create a branch on the git repo which we will use as the id.
    Also resets all chat history files and force tracks them.
    """
    raise NotImplementedError()


@app.post("/listAssistants")
async def list_assistants() -> None:
    """This is going to list all branches with the branch prefix"""
    raise NotImplementedError()


@app.post("/deleteAssistant")
async def delete_assistant() -> None:
    """This is going to delete the branch. Useful if you need to recreate it"""
    raise NotImplementedError()


# Request model
class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 100
    temperature: float = 1.0
    top_p: float = 1.0


# Response model
class CompletionResponse(BaseModel):
    completions: List[str]


@app.post("/completion")
async def generate_completion(request: CompletionRequest) -> CompletionResponse:
    """
    Generate a completion based on the input prompt.

    - **prompt**: The input prompt to generate a completion for.
    - **max_tokens**: Maximum number of tokens to generate (default: 100).
    - **temperature**: Sampling temperature (default: 1.0).
    - **top_p**: Top-p (nucleus sampling) parameter (default: 1.0).
    """
    try:
        # Simulated completion generation logic (replace with your actual logic)
        completions = [f"Generated response for: {request.prompt}"]

        # Return response
        return CompletionResponse(completions=completions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
