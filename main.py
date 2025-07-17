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
    move_uci = move_req.get("uci")
    if not move_uci:
        return JSONResponse(content={"error": "Missing 'uci' move"}, status_code=400)

    if not board.is_legal(chess.Move.from_uci(move_uci)):
        return JSONResponse(content={"error": "Illegal move"}, status_code=400)

    move = chess.Move.from_uci(move_uci)
    if move not in board.legal_moves:
        return JSONResponse(content={"error": "Invalid move"}, status_code=400)

    # Coup du joueur (blancs)
    board.push(move)

    if board.is_game_over():
        return {
            "fen": board.fen(),
            "is_game_over": True,
            "result": board.result()
        }

    # Coup IA (noirs)
    ai_move = choose_ai_move(board)
    board.push(ai_move)

    return {
        "fen": board.fen(),
        "ai_move": ai_move.uci(),
        "is_game_over": board.is_game_over(),
        "result": board.result() if board.is_game_over() else None
    }

def choose_ai_move(board):
    # Ici choix simple : coup aléatoire parmi les coups légaux pour noir
    import random
    moves = list(board.legal_moves)
    return random.choice(moves)

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


