from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import chess
import chess.engine

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

board = chess.Board()

class MoveRequest(BaseModel):
    move_uci: str  # coup en notation UCI, ex: "e2e4"

@app.get("/", response_class=HTMLResponse)
def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/board_state")
def get_board_state():
    # Retourne la position actuelle en FEN et la liste des coups légaux en UCI
    return {
        "fen": board.fen(),
        "legal_moves": [move.uci() for move in board.legal_moves],
        "is_game_over": board.is_game_over(),
        "result": board.result() if board.is_game_over() else None
    }

@app.post("/play_move")
def play_move(move: MoveRequest):
    global board
    try:
        chess_move = chess.Move.from_uci(move.move_uci)
        if chess_move not in board.legal_moves:
            return JSONResponse(status_code=400, content={"error": "Coup illégal"})
        board.push(chess_move)

        # IA joue un coup simple random (plus tard, tu peux intégrer une vraie IA RL)
        import random
        if not board.is_game_over():
            ai_move = random.choice(list(board.legal_moves))
            board.push(ai_move)
        else:
            ai_move = None

        return {
            "fen": board.fen(),
            "ai_move": ai_move.uci() if ai_move else None,
            "is_game_over": board.is_game_over(),
            "result": board.result() if board.is_game_over() else None
        }
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


