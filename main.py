from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import random
import uvicorn
import chess
import requests
import json
import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

board = chess.Board()

# Store all moves in UCI format for saving later
game_moves = []

# --- ADD YOUR GITHUB INFO HERE ---
GITHUB_TOKEN = "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"
REPO_NAME = "Hugoggt/chess-project"
BRANCH = "main"  # or your default branch

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
    return {
        "fen": board.fen(),
        "turn": "white" if board.turn == chess.WHITE else "black",
        "is_check": board.is_check(),
        "is_checkmate": board.is_checkmate(),
        "is_stalemate": board.is_stalemate(),
        "winner": "black" if board.is_checkmate() and board.turn == chess.WHITE else "white" if board.is_checkmate() else None,
        "is_game_over": board.is_game_over(),
    }

def save_game_to_github(moves_list, outcome):
    # Compose filename with timestamp
    now_str = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"saved_games/game_{now_str}.json"

    # Compose game data to save
    data = {
        "moves": moves_list,
        "outcome": outcome,
        "timestamp_utc": now_str,
    }

    # GitHub API URL to create/update a file
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{filename}"

    # First, get the SHA if the file exists (to update)
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    get_resp = requests.get(url, headers=headers)
    sha = None
    if get_resp.status_code == 200:
        sha = get_resp.json().get("sha")

    # Prepare commit message and content
    content_str = json.dumps(data, indent=2)
    content_bytes = content_str.encode("utf-8")
    import base64
    content_b64 = base64.b64encode(content_bytes).decode("utf-8")

    payload = {
        "message": f"Save finished chess game at {now_str}",
        "content": content_b64,
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=headers, json=payload)

    if resp.status_code in [200, 201]:
        print(f"Game saved to GitHub in {filename}")
    else:
        print(f"Failed to save game to GitHub: {resp.status_code} {resp.text}")

@app.post("/move")
def play_move(move: MoveRequest):
    global game_moves

    if board.is_game_over():
        return get_board()

    move_uci = move.from_square + move.to_square
    if move.promotion:
        move_uci += move.promotion.lower()

    try:
        uci_move = chess.Move.from_uci(move_uci)
        if uci_move in board.legal_moves:
            board.push(uci_move)
            game_moves.append(uci_move.uci())

            if not board.is_game_over():
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    comp_move = random.choice(legal_moves)
                    board.push(comp_move)
                    game_moves.append(comp_move.uci())

            # If game just ended, save the full game
            if board.is_game_over():
                # Determine outcome string
                if board.is_checkmate():
                    winner = "black" if board.turn == chess.WHITE else "white"
                    outcome = f"{winner} wins by checkmate"
                elif board.is_stalemate():
                    outcome = "Draw by stalemate"
                elif board.is_insufficient_material():
                    outcome = "Draw by insufficient material"
                elif board.can_claim_threefold_repetition():
                    outcome = "Draw by threefold repetition"
                else:
                    outcome = "Game over"

                save_game_to_github(game_moves, outcome)
                # Reset game_moves for next game
                game_moves = []

    except:
        pass  # ignore illegal or invalid moves

    return get_board()

@app.post("/restart")
def restart_game():
    global board, game_moves
    board = chess.Board()
    game_moves = []
    return get_board()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)









