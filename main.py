from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import random
import uvicorn

import chess
import chess.engine

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

board = chess.Board()

class MoveRequest(BaseModel):
    from_square: str  # like 'e2'
    to_square: str    # like 'e4'
    promotion: Optional[str] = None  # 'q', 'r', 'b', or 'n'

@app.get("/", response_class=HTMLResponse)
def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/board")
def get_board():
    board_state = {
        "fen": board.fen(),
        "turn": "white" if board.turn == chess.WHITE else "black",
        "legal_moves": [move.uci() for move in board.legal_moves],
        "is_check": board.is_check(),
        "is_checkmate": board.is_checkmate(),
        "is_stalemate": board.is_stalemate(),
        "winner": None,
        "is_game_over": board.is_game_over(),
    }
    if board.is_checkmate():
        board_state["winner"] = "black" if board.turn == chess.WHITE else "white"
    return board_state

@app.post("/move")
def play_move(move: MoveRequest):
    if board.is_game_over():
        return get_board()

    move_uci = move.from_square + move.to_square
    if move.promotion:
        move_uci += move.promotion.lower()

    try:
        uci_move = chess.Move.from_uci(move_uci)
        if uci_move in board.legal_moves:
            board.push(uci_move)
            if not board.is_game_over():
                legal = list(board.legal_moves)
                if legal:
                    board.push(random.choice(legal))
    except:
        pass  # Invalid move or format: do nothing

    return get_board()

@app.post("/restart")
def restart_game():
    global board
    board = chess.Board()
    return get_board()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)





