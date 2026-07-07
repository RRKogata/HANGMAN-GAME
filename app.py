"""
Hangman Game - Backend (Flask)
Saari game logic (word choose karna, guess check karna, win/lose decide karna)
yahan Python me hai. Frontend sirf HTML/CSS/JS se render aur display karta hai.
"""

from flask import Flask, render_template, request, jsonify, session
import random
import string

app = Flask(__name__)
app.secret_key = "hangman-secret-key-change-in-production"

# ---------------------------------------------------------
# Word bank - category ke hisaab se words (aap yahan aur words
# add kar sakte ho)
# ---------------------------------------------------------
WORD_BANK = {
    "programming": [
        "python", "flask", "javascript", "developer", "variable",
        "function", "database", "algorithm", "keyboard", "software",
    ],
    "animals": [
        "elephant", "giraffe", "dolphin", "kangaroo", "penguin",
        "crocodile", "butterfly", "octopus", "tiger", "peacock",
    ],
    "countries": [
        "india", "canada", "germany", "brazil", "japan",
        "australia", "egypt", "russia", "france", "nepal",
    ],
}

# Hints for each word
WORD_HINTS = {
    "python": "A popular programming language named after a comedy group",
    "flask": "A lightweight Python web framework",
    "javascript": "The programming language of web browsers",
    "developer": "A person who writes code",
    "variable": "A container for storing data values",
    "function": "A reusable block of code",
    "database": "A place where data is stored",
    "algorithm": "A step-by-step procedure for solving a problem",
    "keyboard": "An input device with letters and numbers",
    "software": "Programs and operating systems",
    "elephant": "The largest land animal",
    "giraffe": "The tallest animal with a long neck",
    "dolphin": "An intelligent marine mammal",
    "kangaroo": "An Australian animal that hops",
    "penguin": "A flightless bird from cold regions",
    "crocodile": "A reptile with sharp teeth",
    "butterfly": "An insect with colorful wings",
    "octopus": "A sea creature with 8 arms",
    "tiger": "A large striped wild cat",
    "peacock": "A bird known for its beautiful tail feathers",
    "india": "Home to the Taj Mahal",
    "canada": "The country north of the USA",
    "germany": "A country in central Europe",
    "brazil": "Famous for Amazon rainforest and carnival",
    "japan": "An island nation in East Asia",
    "australia": "A country that is also a continent",
    "egypt": "Home to the pyramids",
    "russia": "The largest country by area",
    "france": "Home to the Eiffel Tower",
    "nepal": "Home to Mount Everest",
}

MAX_WRONG_GUESSES = 6  # hangman ke 6 stages (head, body, 2 arms, 2 legs)

# Difficulty levels with different hint counts
DIFFICULTY_LEVELS = {
    "easy": {"max_hints": 4, "display_name": "Easy"},
    "medium": {"max_hints": 4, "display_name": "Medium"},
    "hard": {"max_hints": 4, "display_name": "Hard"},
}


def pick_word(category: str) -> str:
    """Category ke hisaab se random word select karta hai."""
    words = WORD_BANK.get(category, WORD_BANK["programming"])
    return random.choice(words).lower()


def build_display_word(word: str, guessed_letters: set) -> str:
    """Word ko underscores ke sath return karta hai, jo letters guess
    ho chuke hain unko show karta hai. Space se separated string."""
    return " ".join([ch if ch in guessed_letters else "_" for ch in word])


def get_game_state():
    """Session se current game state nikaal kar client ko bhejne
    layak dict me convert karta hai."""
    word = session.get("word", "")
    guessed = set(session.get("guessed_letters", []))
    wrong_count = session.get("wrong_count", 0)
    hints_used = session.get("hints_used", 0)
    difficulty = session.get("difficulty", "medium")
    max_hints = DIFFICULTY_LEVELS.get(difficulty, DIFFICULTY_LEVELS["medium"])["max_hints"]

    display_word = build_display_word(word, guessed)
    is_won = "_" not in display_word.replace(" ", "")
    is_lost = wrong_count >= MAX_WRONG_GUESSES
    is_over = is_won or is_lost

    return {
        "display_word": display_word,
        "guessed_letters": sorted(guessed),
        "wrong_count": wrong_count,
        "max_wrong": MAX_WRONG_GUESSES,
        "hints_used": hints_used,
        "max_hints": max_hints,
        "difficulty": difficulty,
        "is_won": is_won,
        "is_lost": is_lost,
        "is_over": is_over,
        # Game khatam hone par hi asli word bhejo (taaki cheating na ho)
        "word": word if is_over else None,
        "category": session.get("category", "programming"),
    }


@app.route("/")
def home():
    """Homepage render karta hai."""
    return render_template("index.html", categories=list(WORD_BANK.keys()))


@app.route("/api/new-game", methods=["POST"])
def new_game():
    """Naya game start karta hai - word select karke session me store karta hai."""
    data = request.get_json(silent=True) or {}
    category = data.get("category", "programming")
    if category not in WORD_BANK:
        category = "programming"
    
    difficulty = data.get("difficulty", "medium")
    if difficulty not in DIFFICULTY_LEVELS:
        difficulty = "medium"

    session["word"] = pick_word(category)
    session["category"] = category
    session["difficulty"] = difficulty
    session["guessed_letters"] = []
    session["wrong_count"] = 0
    session["hints_used"] = 0

    return jsonify(get_game_state())


@app.route("/api/guess", methods=["POST"])
def guess_letter():
    """Ek letter guess karta hai aur updated state return karta hai."""
    if "word" not in session:
        return jsonify({"error": "Koi active game nahi hai. Pehle naya game start karein."}), 400

    data = request.get_json(silent=True) or {}
    letter = (data.get("letter") or "").lower().strip()

    if not letter or letter not in string.ascii_lowercase or len(letter) != 1:
        return jsonify({"error": "Sirf ek valid alphabet letter bhejein (a-z)."}), 400

    state = get_game_state()
    if state["is_over"]:
        return jsonify({"error": "Game already khatam ho chuka hai. Naya game start karein."}), 400

    guessed = set(session.get("guessed_letters", []))

    if letter in guessed:
        # Already guessed - koi penalty nahi, bas current state bhej do
        return jsonify(get_game_state())

    guessed.add(letter)
    session["guessed_letters"] = list(guessed)

    word = session["word"]
    if letter not in word:
        session["wrong_count"] = session.get("wrong_count", 0) + 1

    return jsonify(get_game_state())


@app.route("/api/hint", methods=["POST"])
def get_hint():
    """Ek hint return karta hai (agar available ho to)."""
    if "word" not in session:
        return jsonify({"error": "Koi active game nahi hai. Pehle naya game start karein."}), 400

    word = session["word"]
    hints_used = session.get("hints_used", 0)
    difficulty = session.get("difficulty", "medium")
    max_hints = DIFFICULTY_LEVELS.get(difficulty, DIFFICULTY_LEVELS["medium"])["max_hints"]

    if hints_used >= max_hints:
        return jsonify({"error": f"Aapne sabhi {max_hints} hints use kar diye hain!", "hint": None}), 400

    # Get hint for current word
    hint = WORD_HINTS.get(word, "No hint available for this word")

    session["hints_used"] = hints_used + 1

    return jsonify({
        "hint": hint,
        "hints_used": session["hints_used"],
        "hints_remaining": max_hints - session["hints_used"]
    })


@app.route("/api/state", methods=["GET"])
def state():
    """Current game state return karta hai (page reload ke liye useful)."""
    if "word" not in session:
        return jsonify({"active": False})
    result = get_game_state()
    result["active"] = True
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)