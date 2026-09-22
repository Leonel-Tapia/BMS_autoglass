from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from sqlalchemy import text

router = APIRouter(
    prefix="/zipcodes",
    tags=["Zip Codes"]
)

@router.get("/search")
def search_zipcodes(q: str, db: Session = Depends(get_db)):
    query = text("""
        SELECT zip_code, city, state
        FROM zipcodes
        WHERE zip_code LIKE :pattern
        ORDER BY zip_code
        LIMIT 20
    """)

    result = db.execute(query, {"pattern": f"{q}%"})
    rows = result.fetchall()

    return [
        {
            "zip_code": r.zip_code,
            "city": r.city,
            "state": r.state
        }
        for r in rows
    ]
