import os
from flask import Flask, request, redirect, session, jsonify
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

token_info_global = None


@app.route("/")
def home():
    return "Witaj w Sophiza AI 🌙 Przejdź do /login, by zalogować się do Spotify."


@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route("/callback")
def callback():
    global token_info_global
    code = request.args.get("code")
    token_info_global = sp_oauth.get_access_token(code)
    return "Autoryzacja zakończona sukcesem. Możesz teraz dodać utwór."


@app.route("/add_song", methods=["POST"])
def add_song():
    global token_info_global
    if not token_info_global:
        return jsonify({"error": "Brak tokena. Najpierw zaloguj się."}), 403

    access_token = token_info_global["access_token"]
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
    global token_info_global
    if not token_info_global:
        return jsonify({"error": "Brak tokena. Najpierw zaloguj się."}), 403

    access_token = token_info_global["access_token"]
    sp = Spotify(auth=access_token)

    data = request.get_json()
    mood_text = data.get("mood", "").lower()

    mood_map = {
        "smutna": "Daughter – Youth",
        "pusta": "AURORA – Runaway",
        "nostalgia": "Lana Del Rey – Video Games",
        "radość": "Vance Joy – Riptide",
        "nadzieja": "Coldplay – Paradise",
        "miłość": "Ben Howard – Only Love",
        "zmęczenie": "Riverside – Lost (Why Should I Be Frightened by a Hat?)",
        "bezsilność": "Agnes Obel – Dorian"
    }

    song = mood_map.get(mood_text, "Sleeping at Last – Saturn")

    results = sp.search(q=song, limit=1, type="track")
    if not results["tracks"]["items"]:
        return jsonify({"error": f"Nie znaleziono utworu: {song}"}), 404

    track_id = results["tracks"]["items"][0]["id"]
    playlist_id = "2R9BQWb8j1wL9YxHk4soxT"
    sp.playlist_add_items(playlist_id, [track_id])

    return jsonify({"message": f"Dodałam utwór: {song}"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
