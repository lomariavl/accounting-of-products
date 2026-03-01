import datetime

from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, text
from starlette.staticfiles import StaticFiles

from db import create_db_and_tables
from db import get_session

app = FastAPI()
templates = Jinja2Templates(directory='templates')
app.mount("/imgs", StaticFiles(directory="/imgs"), name="imgs")


@app.on_event('startup')
def on_startup():
    create_db_and_tables()


@app.get('/')
def read_table(request: Request, db: Session = Depends(get_session)):
    query = """
       SELECT
            created_at,
            username,
            comment,
            SUM(CASE WHEN ab = 'a' THEN quantity END) AS a,
            SUM(CASE WHEN ab = 'b' THEN quantity END) AS b,
            SUM(CASE WHEN ab = 'bp' THEN quantity END) AS bp,
            photo_path
        FROM storage
        GROUP BY created_at, username, comment, photo_path
        ORDER BY created_at DESC;"""
    rows = db.connection().execute(text(query)).all()
    items = []
    for row in rows:
        d = dict(row._mapping)

        if isinstance(d.get("created_at"), (datetime.date, datetime.datetime)):
            d["created_at"] = d["created_at"].isoformat()

        items.append(d)
    print(items)

    return templates.TemplateResponse("table.html", {
        "request": request,
        "items": items
    })
