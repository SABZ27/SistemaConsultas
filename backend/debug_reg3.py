import os
os.environ['DB_URL'] = 'sqlite+pysqlite:///./test_bd_debug3.sqlite3'
os.environ['ADMIN_CORREO'] = 'admin@test.com'
os.environ['ADMIN_PASSWORD'] = 'contrasenia123'
os.environ['ADMIN_IDENTIFICACION'] = '9000000000'
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import engine, SessionLocal
from app.models import Base
from app.db.seeds import ejecutar_seeds
Base.metadata.create_all(bind=engine)
s = SessionLocal()
ejecutar_seeds(s)
s.commit(); s.close()
c = TestClient(app)
r = c.post('/auth/register', json={'identificacion':'1000000001','nombre':'Nombre1','apellido':'Apellido','correo':'estudiante@test.com','password':'contrasenia123','rol':'ESTUDIANTE'})
print(r.status_code)
print(r.json())
