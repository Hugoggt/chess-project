from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import random
import uvicorn
import chess
import os
import requests
from datetime import datetime

# === CONFIGURE THESE ===
GITHUB_TOKEN = "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"
REPO_NAME = "Hugoggt/chess-project"

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

board = chess.Board()

class MoveRequest(BaseModel):
    from_square: str  # like 'e2'
    to_square: str    # like 'e4'
    promotion: Optional[str] = None  # 'q', 'r', 'b', or 'n'

def save_game_to_github():
    """Save finished game to GitHub under saved_games/ folder."""
    result = None
    if board.is_checkmate():
        result = "White wins" if board.turn == chess.BLACK else "Black wins"
    elif board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
        result = "Draw"

    if not result:
        return

    scenario = board.fen()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"saved_games/game_{timestamp}.txt"
    content = f"Result: {result}\nFEN: {scenario}\n\nPGN:\n{board.board_fen()}"

    # Create the file in the repo
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{filename}"
    data = {
        "message": f"Save finished game {timestamp}",
        "content": content.encode("utf-8").decode("utf-8"),  # temporarily keep text
    }

    # GitHub API expects Base64 encoding for "content"
    import base64
    data["content"] = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.put(url, json=data, headers=headers)

    if r.status_code not in (200, 201):
        print("Failed to save game to GitHub:", r.text)

@app.get("/", response_class=HTMLResponse)
def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/board")
def get_board():
    return {
        "fen": board.fen(),
        "turn": "white" if board.turn == chess.WHITE else "black",
        "is_check": board.is_check(),
        "is_checkmate": board.is_checkmate(),
        "is_stalemate": board.is_stalemate(),
        "winner": "black" if board.is_checkmate() and board.turn == chess.WHITE else "white" if board.is_checkmate() else None,
        "is_game_over": board.is_game_over(),
    }

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
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    board.push(random.choice(legal_moves))
    except:
        pass  # ignore illegal or invalid moves

    if board.is_game_over():
        save_game_to_github()

    return get_board()

@app.post("/restart")
def restart_game():
    global board
    board = chess.Board()
    return get_board()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)









