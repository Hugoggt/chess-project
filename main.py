import os
import json
import requests
import chess
import chess.pgn
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from io import StringIO

app = Flask(__name__)

# Your GitHub configuration
GITHUB_REPO = "Hugoggt/chess-project"  # <-- change to your repo
GITHUB_BRANCH = "main"  # or "master"
GITHUB_TOKEN = os.getenv("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")  # Make sure your Render env variable matches
SAVE_FOLDER = "saved_games"  # must exist in your repo

# Chess game state
games = {}  # game_id -> {"board": chess.Board(), "history": []}

def save_game_to_github(game_id, game):
    """
    Save the game PGN to GitHub under saved_games folder
    """
    # Prepare PGN from history
    pgn_io = StringIO()
    chess_game = chess.pgn.Game()
    node = chess_game

    for move_uci in game["history"]:
        move = game["board"].parse_uci(move_uci)
        node = node.add_variation(move)

    chess_game.headers["Event"] = "Online Chess Game"
    chess_game.headers["Date"] = datetime.utcnow().strftime("%Y.%m.%d")
    chess_game.headers["Result"] = game["board"].result()

    print("[DEBUG] Preparing PGN for game:", game_id)
    print(chess_game)

    # Convert to PGN text
    pgn_text = str(chess_game)

    # Define GitHub file path
    filename = f"{SAVE_FOLDER}/game_{game_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pgn"

    # GitHub API endpoint
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"

    # Prepare commit
    commit_message = f"Add finished game {game_id}"
    content_encoded = pgn_text.encode("utf-8")
    import base64
    content_b64 = base64.b64encode(content_encoded).decode("utf-8")

    # API request
    response = requests.put(
        url,
        headers={
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        },
        json={
            "message": commit_message,
            "content": content_b64,
            "branch": GITHUB_BRANCH
        }
    )

    if response.status_code in (200, 201):
        print(f"[SUCCESS] Game saved to GitHub: {filename}")
    else:
        print(f"[ERROR] Failed to save game: {response.status_code}")
        print(response.text)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start_game", methods=["POST"])
def start_game():
    game_id = str(len(games) + 1)
    games[game_id] = {"board": chess.Board(), "history": []}
    return jsonify({"game_id": game_id, "fen": games[game_id]["board"].fen()})


@app.route("/move", methods=["POST"])
def move():
    data = request.get_json()
    game_id = data.get("game_id")
    move_uci = data.get("move")

    if game_id not in games:
        return jsonify({"error": "Game not found"}), 404

    board = games[game_id]["board"]

    try:
        move = board.parse_uci(move_uci)
        if move not in board.legal_moves:
            return jsonify({"error": "Illegal move"}), 400
        board.push(move)
        games[game_id]["history"].append(move_uci)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    # Check game end
    if board.is_game_over():
        save_game_to_github(game_id, games[game_id])

    return jsonify({"fen": board.fen(), "game_over": board.is_game_over()})


if __name__ == "__main__":
    app.run(debug=True)









