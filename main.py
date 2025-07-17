from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Représente l'échiquier (chaque case peut contenir une pièce sous forme de string)
# Exemple : 'wP' = pion blanc, 'bK' = roi noir, '' = vide
board = [
    ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
    ['bP'] * 8,
    [''] * 8,
    [''] * 8,
    [''] * 8,
    [''] * 8,
    ['wP'] * 8,
    ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']
]

# Pour suivre les tours
turn = 'w'

class MoveRequest(BaseModel):
    from_row: int
    from_col: int
    to_row: int
    to_col: int

@app.get("/", response_class=HTMLResponse)
def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/board")
def get_board():
    return {"board": board, "turn": turn}

@app.post("/move")
def play_move(move: MoveRequest):
    global board, turn
    piece = board[move.from_row][move.from_col]
    if not piece or piece[0] != turn:
        return JSONResponse(content={"error": "Coup invalide"}, status_code=400)
    
    if not is_valid_move(piece, move.from_row, move.from_col, move.to_row, move.to_col):
        return JSONResponse(content={"error": "Mouvement illégal"}, status_code=400)

    board[move.to_row][move.to_col] = piece
    board[move.from_row][move.from_col] = ''
    turn = 'b' if turn == 'w' else 'w'
    return {"board": board, "turn": turn}

def is_valid_move(piece, fr, fc, tr, tc):
    target = board[tr][tc]
    if target and target[0] == piece[0]:
        return False  # on ne peut pas capturer une pièce alliée

    dx, dy = tr - fr, tc - fc
    name = piece[1]

    def clear_path():
        step_r = (dx > 0) - (dx < 0)
        step_c = (dy > 0) - (dy < 0)
        r, c = fr + step_r, fc + step_c
        while r != tr or c != tc:
            if board[r][c] != '':
                return False
            r += step_r
            c += step_c
        return True

    if name == 'P':  # pion
        direction = -1 if piece[0] == 'w' else 1
        start_row = 6 if piece[0] == 'w' else 1
        if fc == tc and board[tr][tc] == '':
            if tr - fr == direction:
                return True
            if fr == start_row and tr - fr == 2 * direction and board[fr + direction][fc] == '':
                return True
        if abs(fc - tc) == 1 and tr - fr == direction and board[tr][tc] != '':
            return True
    elif name == 'R':  # tour
        if fr == tr or fc == tc:
            return clear_path()
    elif name == 'B':  # fou
        if abs(dx) == abs(dy):
            return clear_path()
    elif name == 'Q':  # reine
        if fr == tr or fc == tc or abs(dx) == abs(dy):
            return clear_path()
    elif name == 'N':  # cavalier
        return (abs(dx), abs(dy)) in [(1, 2), (2, 1)]
    elif name == 'K':  # roi
        return max(abs(dx), abs(dy)) == 1
    return False

if __name__ == "__main__":
    try:
        uvicorn.run("main:app", port=8000, reload=True)
    except Exception as e:
        print(f"Erreur lors du lancement du serveur : {e}")



