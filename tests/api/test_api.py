"""
Here we are going to test the API as a uvicorn server.
"""
import completion
import import
import litellm

ADDRESS = "localhost"

from multiprocessing import Process

import pytest
import uvicorn

from aider.api import app

ADDRESS = "http://localhost:8000"
def run_server():
    uvicorn.run(app)


@pytest.fixture
def server():
    proc = Process(target=run_server, args=(), daemon=True)
    proc.start() 
    yield
    proc.kill() # Cleanup after test


def test_read_main(server):
    out = completion(model="openai/gpt-4o", messages=messages)
