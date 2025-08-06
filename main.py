from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict
import random
import uvicorn
import uuid
import chess
import chess.pgn
import os
from io import StringIO

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure directory for saving games exists
os.makedirs("saved_games", exist_ok=True)

# Game storage
games: Dict[str, chess.Board] = {}
game_history: Dict[str, chess.pgn.Game] = {}

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
    board = chess.Board()
    game = chess.pgn.Game()
    game.headers["Event"] = "FastAPI Chess Game"
    game.setup(board)
    games[game_id] = board
    game_history[game_id] = game
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
    game = game_history.get(move.game_id)

    if not board or board.is_game_over():
        return get_board(move.game_id)

    move_uci = move.from_square + move.to_square
    from_sq = chess.parse_square(move.from_square)
    to_sq = chess.parse_square(move.to_square)
    piece = board.piece_at(from_sq)

    # Handle promotion
    if piece and piece.piece_type == chess.PAWN and (chess.square_rank(to_sq) == 0 or chess.square_rank(to_sq) == 7):
        if move.promotion:
            move_uci += move.promotion.lower()
        else:
            return {"error": "Promotion required"}

    try:
        uci_move = chess.Move.from_uci(move_uci)
        if uci_move in board.legal_moves:
            board.push(uci_move)
            game = record_move(game, uci_move)

            # AI Move
            if not board.is_game_over():
                legal_moves = list(board.legal_moves)
                if legal_moves:
                    ai_move = random.choice(legal_moves)
                    board.push(ai_move)
                    game = record_move(game, ai_move)
    except:
        pass

    # Save game if it's over
    if board.is_game_over():
        print("a")
        save_game_to_file(move.game_id, game)
        print("a")

    return get_board(move.game_id)

def record_move(game: chess.pgn.Game, move: chess.Move) -> chess.pgn.Game:
    if game is None:
        return None
    node = game
    while node.variations:
        node = node.variations[0]
    return node.add_variation(move).game()

def save_game_to_file(game_id: str, game: chess.pgn.Game):
    filepath = f"saved_games/{game_id}.pgn"
    with open(filepath, "w", encoding="utf-8") as f:
        exporter = chess.pgn.FileExporter(f)
        game.accept(exporter)

@app.post("/restart/{game_id}")
def restart_game(game_id: str):
    board = chess.Board()
    game = chess.pgn.Game()
    game.headers["Event"] = "FastAPI Chess Game"
    game.setup(board)
    games[game_id] = board
    game_history[game_id] = game
    return get_board(game_id)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)








