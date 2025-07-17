from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import chess
import random

app = FastAPI()

board = chess.Board()

app.mount("/static", StaticFiles(directory="static"), name="static")

class MoveRequest(BaseModel):
    uci: str

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

        if board.is_game_over():
            return {
                "fen": board.fen(),
                "ai_move": None,
                "is_game_over": True,
                "result": board.result()
            }

        ai_move = random.choice(list(board.legal_moves))
        board.push(ai_move)

        return {
            "fen": board.fen(),
            "ai_move": ai_move.uci(),
            "is_game_over": board.is_game_over(),
            "result": board.result() if board.is_game_over() else None
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


