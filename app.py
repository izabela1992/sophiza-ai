import os
import json
from flask import Flask, request, redirect, jsonify
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "supersekretklucz"
app.config["SESSION_COOKIE_NAME"] = "SophiSession"

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SCOPE = "playlist-modify-public"

sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
)

TOKEN_FILE = "token.json"

def save_token(token_info):
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_info, f)

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None

@app.route("/")
def home():
    return "Witaj w Sophiza AI 🌙 Przejdź do /login, by zalogować się do Spotify."

@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code=code, as_dict=True)
    save_token(token_info)
    return "Autoryzacja zakończona sukcesem. Możesz teraz dodać utwór."

@app.route("/add_song", methods=["POST"])
def add_song():
    token_info = load_token()
    if not token_info:
        return jsonify({"error": "Brak tokena. Najpierw zaloguj się."}), 403

    access_token = token_info["access_token"]
    sp = Spotify(auth=access_token)

    data = request.get_json()
    song_name = data.get("song_name")
    playlist_id = "2R9BQWb8j1wL9YxHk4soxT"

    results = sp.search(q=song_name, limit=1, type="track")
    if not results["tracks"]["items"]:
        return jsonify({"error": "Nie znaleziono utworu"}), 404

    track_id = results["tracks"]["items"][0]["id"]
    sp.playlist_add_items(playlist_id, [track_id])
    return jsonify({"message": f"Utwór '{song_name}' dodany do playlisty."})

@app.route("/mood_song", methods=["POST"])
def mood_song():
    token_info = load_token()
    if not token_info:
        return jsonify({"error": "Brak tokena. Najpierw zaloguj się."}), 403

    access_token = token_info["access_token"]
    sp = Spotify(auth=access_token)

    data = request.get_json()
    mood_text = data.get("mood", "").lower()

    results = sp.search(q=mood_text, limit=10, type="track")
    tracks = results.get("tracks", {}).get("items", [])

    if not tracks:
        return jsonify({"error": f"Nie znalazłam utworu pasującego do: {mood_text}"}), 404

    playlist_id = "2R9BQWb8j1wL9YxHk4soxT"
    existing_tracks = sp.playlist_tracks(playlist_id)
    existing_ids = [item["track"]["id"] for item in existing_tracks["items"]]

    new_track = next((track for track in tracks if track["id"] not in existing_ids), None)

    if not new_track:
        return jsonify({"error": "Nie znalazłam nowej piosenki, która nie byłaby już na playliście."}), 400

    sp.playlist_add_items(playlist_id, [new_track["id"]])
    return jsonify({"message": f"Dodałam: {new_track['name']} – {new_track['artists'][0]['name']} do playlisty."})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
