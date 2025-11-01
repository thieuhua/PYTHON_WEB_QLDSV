from backend.db.database import SessionLocal
from backend.db import models
#Chay cau lenh duoi trong terminal de xem cac bang trong database
#python -m backend.db.show_db 
def show_table():
    db = SessionLocal()
    try:
        #Co the thay Grade bang ten cac Table khac trong database de in ra table do
        #Sau khi thay doi nho save file
        rows = db.query(models.JoinCode).all()
        for row in rows:
            print(row.__dict__)
    finally:
        db.close()

if __name__ == "__main__":
    show_table()
