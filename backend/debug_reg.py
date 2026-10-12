import os
os.environ.setdefault('DB_URL','sqlite+pysqlite:///./test_bd_debug.sqlite3')
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
c = TestClient(app)
r = c.post('/auth/register', json={'identificacion':'1000000001','nombre':'Nombre1','apellido':'Apellido','correo':'estudiante@test.com','password':'contrasenia123','rol':'ESTUDIANTE'})
print(r.status_code)
print(r.json())
