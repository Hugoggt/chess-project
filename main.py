from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict
import random
import uvicorn
import uuid
import chess

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

games: Dict[str, chess.Board] = {}

class MoveRequest(BaseModel):
    game_id: str
    from_square: str
    to_square: str
    promotion: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/start")
def start_game():
    game_id = str(uuid.uuid4())
    games[game_id] = chess.Board()
    return {"game_id": game_id}

@app.get("/board/{game_id}")
def get_board(game_id: str):
    board = games.get(game_id)
    if not board:
        return {"error": "Game not found"}
    return {
        "fen": board.fen(),
        "turn": "white" if board.turn == chess.WHITE else "black",
        "is_check": board.is_check(),
        "is_checkmate": board.is_checkmate(),
        "is_stalemate": board.is_stalemate(),
        "winner": "black" if board.is_checkmate() and board.turn == chess.WHITE else "white" if board.is_checkmate() else None,
        "is_game_over": board.is_game_over(),
        "promotion_rank": 6 if board.turn == chess.WHITE else 1
    }

@app.post("/move")
def play_move(move: MoveRequest):
    board = games.get(move.game_id)
    if not board or board.is_game_over():
        return get_board(move.game_id)

    move_uci = move.from_square + move.to_square
    from_sq = chess.parse_square(move.from_square)
    to_sq = chess.parse_square(move.to_square)
    piece = board.piece_at(from_sq)

    # Handle promotion properly
    if piece and piece.piece_type == chess.PAWN and (chess.square_rank(to_sq) == 0 or chess.square_rank(to_sq) == 7):
        if move.promotion:
            move_uci += move.promotion.lower()
        else:
            return {"error": "Promotion required"}

    try:
        uci_move = chess.Move.from_uci(move_uci)
        if uci_move in board.legal_moves:
            board.push(uci_move)
            # AI move
            if not board.is_game_over():
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    board.push(random.choice(legal_moves))
    except:
        pass

    return get_board(move.game_id)

@app.post("/restart/{game_id}")
def restart_game(game_id: str):
    games[game_id] = chess.Board()
    return get_board(game_id)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)








