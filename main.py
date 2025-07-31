from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


# Piece classes and board logic
class Piece:
    def __init__(self, color):
        self.color = color

    def legal_moves(self, board, x, y):
        return []

class King(Piece):
    def __str__(self): return "K" if self.color == "white" else "k"

class Queen(Piece):
    def __str__(self): return "Q" if self.color == "white" else "q"

class Rook(Piece):
    def __str__(self): return "R" if self.color == "white" else "r"

class Bishop(Piece):
    def __str__(self): return "B" if self.color == "white" else "b"

class Knight(Piece):
    def __str__(self): return "N" if self.color == "white" else "n"

class Pawn(Piece):
    def __str__(self): return "P" if self.color == "white" else "p"


class Game:
    def __init__(self):
        self.reset_board()

    def reset_board(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.turn = "white"

        # Setup pawns
        for i in range(8):
            self.board[1][i] = Pawn("black")
            self.board[6][i] = Pawn("white")

        # Setup other pieces
        order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for i, cls in enumerate(order):
            self.board[0][i] = cls("black")
            self.board[7][i] = cls("white")

    def get_board_state(self):
        return [[str(piece) if piece else "" for piece in row] for row in self.board]

    def move(self, fx, fy, tx, ty):
        piece = self.board[fy][fx]
        if not piece or piece.color != self.turn:
            return False
        self.board[ty][tx] = piece
        self.board[fy][fx] = None
        self.turn = "black" if self.turn == "white" else "white"
        return True


game = Game()


class MoveRequest(BaseModel):
    from_x: int
    from_y: int
    to_x: int
    to_y: int


@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html") as f:
        return f.read()


@app.get("/board")
def get_board():
    return {"board": game.get_board_state(), "turn": game.turn}


@app.post("/move")
def make_move(move: MoveRequest):
    success = game.move(move.from_x, move.from_y, move.to_x, move.to_y)
    return {"success": success, "board": game.get_board_state(), "turn": game.turn}


@app.post("/restart")
def restart():
    game.reset_board()
    return {"board": game.get_board_state(), "turn": game.turn}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)









