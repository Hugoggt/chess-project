from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import chess
import chess.engine

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

board = chess.Board()  # partie globale (attention en vrai multi-user il faut autre chose !)

class MoveRequest(BaseModel):
    uci: str  # mouvement en notation UCI, ex: e2e4

@app.get("/", response_class=HTMLResponse)
def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/board")
def get_board():
    return {"fen": board.fen(), "is_game_over": board.is_game_over(), "result": board.result() if board.is_game_over() else None}

@app.post("/move")
def play_move(move_req: dict):
    try:
        # suppose on fait un truc qui peut échouer
        move = move_req.get("uci")
        if move is None:
            raise ValueError("Missing move")
        # ici, ta logique pour jouer le coup
        return {"status": "move played", "move": move}
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

def choose_ai_move(board):
    try:
        moves = list(board.legal_moves)
        if not moves:
            return None
        return random.choice(moves)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


