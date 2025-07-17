from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Plateau d'échecs
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

# Couleur du joueur actuel ('w' ou 'b')
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

    if turn is None:
        return JSONResponse(content={"error": "Partie terminée"}, status_code=400)

    piece = board[move.from_row][move.from_col]
    if not piece or piece[0] != turn:
        return JSONResponse(content={"error": "Coup invalide"}, status_code=400)

    if not is_valid_move(piece, move.from_row, move.from_col, move.to_row, move.to_col):
        return JSONResponse(content={"error": "Mouvement illégal"}, status_code=400)

    # Appliquer le coup
    board[move.to_row][move.to_col] = piece
    board[move.from_row][move.from_col] = ''

    # Vérifier échec / mat
    next_turn = 'b' if turn == 'w' else 'w'

    if is_in_check(next_turn):
        if not has_legal_moves(next_turn):
            winner = "Blancs" if turn == 'w' else "Noirs"
            turn = None
            return {"board": board, "turn": None, "status": f"Échec et mat. {winner} gagnent !"}
        else:
            turn = next_turn
            return {"board": board, "turn": turn, "status": "Échec !"}

    if not has_legal_moves(next_turn):
        turn = None
        return {"board": board, "turn": None, "status": "Pat. Match nul."}

    turn = next_turn
    return {"board": board, "turn": turn, "status": ""}

def is_valid_move(piece, fr, fc, tr, tc, ignore_check=False):
    target = board[tr][tc]

    # ← CORRECTION ICI
    if not ignore_check and target and target[0] == piece[0]:
        return False

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

    valid = False
    if name == 'P':
        direction = -1 if piece[0] == 'w' else 1
        start_row = 6 if piece[0] == 'w' else 1
        if fc == tc and board[tr][tc] == '':
            if tr - fr == direction:
                valid = True
            elif fr == start_row and tr - fr == 2 * direction and board[fr + direction][fc] == '':
                valid = True
        elif abs(fc - tc) == 1 and tr - fr == direction and board[tr][tc] != '':
            valid = True
    elif name == 'R':
        valid = (fr == tr or fc == tc) and clear_path()
    elif name == 'B':
        valid = abs(dx) == abs(dy) and clear_path()
    elif name == 'Q':
        valid = (fr == tr or fc == tc or abs(dx) == abs(dy)) and clear_path()
    elif name == 'N':
        valid = (abs(dx), abs(dy) in [(1, 2), (2, 1)])
    elif name == 'K':
        valid = max(abs(dx), abs(dy)) == 1

    if not valid:
        return False

    if ignore_check:
        return True

    # Vérifie que le coup ne met pas notre roi en échec
    saved_from, saved_to = board[fr][fc], board[tr][tc]
    board[tr][tc] = piece
    board[fr][fc] = ''
    in_check = is_in_check(piece[0])
    board[fr][fc] = saved_from
    board[tr][tc] = saved_to
    return not in_check


def is_in_check(color):
    king_pos = find_king(color)
    if not king_pos:
        return True
    kr, kc = king_pos
    opponent = 'b' if color == 'w' else 'w'

    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece and piece[0] == opponent:
                if is_valid_move(piece, r, c, kr, kc, ignore_check=True):
                    return True
    return False

def has_legal_moves(color):
    for fr in range(8):
        for fc in range(8):
            piece = board[fr][fc]
            if piece and piece[0] == color:
                for tr in range(8):
                    for tc in range(8):
                        if is_valid_move(piece, fr, fc, tr, tc):
                            return True
    return False

def find_king(color):
    for r in range(8):
        for c in range(8):
            if board[r][c] == color + 'K':
                return r, c
    return None

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)



