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
        move = move_req.get("uci")
        if move is None:
            raise ValueError("Missing move")

        # Jouer le coup du joueur
        board.push(chess.Move.from_uci(move))

        # Vérifier si la partie est finie après le coup du joueur
        if board.is_game_over():
            return {
                "fen": board.fen(),
                "is_game_over": True,
                "result": board.result()
            }

        # Coup de l'IA (joue noir)
        ai_move = choose_ai_move(board)
        board.push(ai_move)

        # Vérifier si la partie est finie après le coup de l'IA
        return {
            "fen": board.fen(),
            "ai_move": ai_move.uci(),
            "is_game_over": board.is_game_over(),
            "result": board.result() if board.is_game_over() else None
        }

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

def choose_ai_move(board):
    # Ici choix simple : coup aléatoire parmi les coups légaux pour noir
    import random
    moves = list(board.legal_moves)
    return random.choice(moves)

    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


