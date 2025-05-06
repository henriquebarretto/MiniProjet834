# test/test_websocket.py
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app  

client = TestClient(app)

def test_websocket_echo():
    with client.websocket_connect("/ws/alice") as ws1, \
         client.websocket_connect("/ws/bob") as ws2:

        ws1.send_text("Salut Bob !")
        data = ws2.receive_text()

        assert data == "alice : Salut Bob !"

