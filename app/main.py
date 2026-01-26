from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, text

from db import get_session, Storage
from db import create_db_and_tables

app = FastAPI()
templates = Jinja2Templates(directory='templates')


@app.on_event('startup')
def on_startup():
    create_db_and_tables()


@app.get('/')
def read_table(request: Request, db: Session = Depends(get_session)):
    query = """
       SELECT
            created_at,
            username,
            SUM(CASE WHEN ab = 'A' THEN quantity END) AS A,
            SUM(CASE WHEN ab = 'B' THEN quantity END) AS B,
            SUM(CASE WHEN ab = 'A1' THEN quantity END) AS A1,
            SUM(CASE WHEN ab = 'B1' THEN quantity END) AS B1
        FROM storage
        GROUP BY created_at, username
        ORDER BY created_at, username;"""
    items = db.connection().execute(text(query)).all()
    print(items)

    return templates.TemplateResponse("table.html", {
        "request": request,
        "items": items
    })
