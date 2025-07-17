from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

app = FastAPI()

# Lier le dossier 'static' pour servir du HTML
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def serve_homepage():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


# Créer l'endpoint API pour doubler un nombre
class NumberRequest(BaseModel):
    number: int

@app.post("/double")
def double_number(data: NumberRequest):
    return {"result": data.number * 2}

