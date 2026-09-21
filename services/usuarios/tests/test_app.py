from fastapi.testclient import TestClient  

from usuarios.app import app  

client = TestClient(app)
