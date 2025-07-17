from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import chess
import random

app = FastAPI()

# Crée une instance du plateau
board = chess.Board()

# Sert les fichiers statiques (HTML, JS, CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

class MoveRequest(BaseModel):
    uci: str  # exemple : "e2e4"

@app.get("/", response_class=HTMLResponse)
def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/board")
def get_board():
    return {
        "fen": board.fen(),
        "is_game_over": board.is_game_over(),
        "result": board.result() if board.is_game_over() else None
    }

@app.post("/move")
def play_move(move_req: MoveRequest):
    try:
        move = chess.Move.from_uci(move_req.uci)
        if move not in board.legal_moves:
            raise ValueError("Coup illégal")
        board.push(move)

        # Vérifie si le jeu est fini après le coup du joueur
        if board.is_game_over():
            return {
                "fen": board.fen(),
                "ai_move": None,
                "is_game_over": True,
                "result": board.result()
            }

        # Coup IA
        ai_move = choose_ai_move(board)
        if ai_move is not None:
            board.push(ai_move)

        return {
            "fen": board.fen(),
            "ai_move": ai_move.uci() if ai_move else None,
            "is_game_over": board.is_game_over(),
            "result": board.result() if board.is_game_over() else None
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

def choose_ai_move(board):
    moves = list(board.legal_moves)
    return random.choice(moves) if moves else None


