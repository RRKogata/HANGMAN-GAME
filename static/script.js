// Hangman Game - Frontend logic
// Saara actual game logic (word choose karna, sahi/galat guess check karna)
// backend (Flask, Python) me hai. Yeh file sirf API call karke UI update karti hai.

const wordDisplayEl = document.getElementById("wordDisplay");
const statusMessageEl = document.getElementById("statusMessage");
const hintDisplayEl = document.getElementById("hintDisplay");
const wrongCountEl = document.getElementById("wrongCount");
const maxWrongEl = document.getElementById("maxWrong");
const keyboardEl = document.getElementById("keyboard");
const newGameBtn = document.getElementById("newGameBtn");
const hintBtn = document.getElementById("hintBtn");
const categorySelect = document.getElementById("category");
const difficultySelect = document.getElementById("difficulty");

const bodyParts = [
  "part-head",
  "part-body",
  "part-arm-left",
  "part-arm-right",
  "part-leg-left",
  "part-leg-right",
];

const ALPHABET = "abcdefghijklmnopqrstuvwxyz".split("");

function buildKeyboard() {
  keyboardEl.innerHTML = "";
  ALPHABET.forEach((letter) => {
    const btn = document.createElement("button");
    btn.textContent = letter;
    btn.className = "key-btn";
    btn.dataset.letter = letter;
    btn.addEventListener("click", () => handleGuess(letter));
    keyboardEl.appendChild(btn);
  });
}

function updateHangmanDrawing(wrongCount) {
  bodyParts.forEach((partId, index) => {
    const el = document.getElementById(partId);
    if (index < wrongCount) {
      el.classList.remove("hidden");
      el.classList.add("visible");
    } else {
      el.classList.add("hidden");
      el.classList.remove("visible");
    }
  });
}

function updateKeyboardState(guessedLetters, correctWord) {
  document.querySelectorAll(".key-btn").forEach((btn) => {
    const letter = btn.dataset.letter;
    btn.classList.remove("correct", "wrong");
    if (guessedLetters.includes(letter)) {
      btn.disabled = true;
      if (correctWord && correctWord.includes(letter)) {
        btn.classList.add("correct");
      } else {
        btn.classList.add("wrong");
      }
    } else {
      btn.disabled = false;
    }
  });
}

function renderState(state) {
  wordDisplayEl.textContent = state.display_word;
  wrongCountEl.textContent = state.wrong_count;
  maxWrongEl.textContent = state.max_wrong;
  updateHangmanDrawing(state.wrong_count);
  updateKeyboardState(state.guessed_letters, state.word);

  // Update hint button state
  hintBtn.disabled = state.hints_used >= state.max_hints || state.is_over;
  
  // Clear hint display
  hintDisplayEl.textContent = "";

  statusMessageEl.className = "status-message";
  if (state.is_won) {
    statusMessageEl.textContent = "🎉 Badhai ho! Aapne word sahi guess kar liya!";
    statusMessageEl.classList.add("win");
    disableAllKeys();
  } else if (state.is_lost) {
    statusMessageEl.textContent = `😢 Game over! Sahi word tha: "${state.word}"`;
    statusMessageEl.classList.add("lose");
    disableAllKeys();
  } else {
    statusMessageEl.textContent = "";
  }
}

function disableAllKeys() {
  document.querySelectorAll(".key-btn").forEach((btn) => (btn.disabled = true));
}

async function startNewGame() {
  const category = categorySelect.value;
  const difficulty = difficultySelect.value;
  const res = await fetch("/api/new-game", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ category, difficulty }),
  });
  const state = await res.json();
  buildKeyboard();
  hintBtn.textContent = `💡 Hint (${state.max_hints})`;
  hintBtn.disabled = false;
  hintDisplayEl.textContent = "";
  renderState(state);
}

async function handleGuess(letter) {
  const res = await fetch("/api/guess", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ letter }),
  });
  const state = await res.json();
  if (state.error) {
    console.warn(state.error);
    return;
  }
  renderState(state);
}

async function handleHint() {
  const res = await fetch("/api/hint", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  const data = await res.json();
  if (data.error) {
    hintDisplayEl.textContent = `⚠️ ${data.error}`;
    return;
  }
  hintDisplayEl.textContent = `💡 Hint: ${data.hint}`;
  
  // Update button to reflect remaining hints
  const hintsRemaining = data.hints_remaining;
  if (hintsRemaining > 0) {
    hintBtn.textContent = `💡 Hint (${hintsRemaining})`;
  } else {
    hintBtn.disabled = true;
  }
}

// Physical keyboard support
document.addEventListener("keydown", (e) => {
  const key = e.key.toLowerCase();
  if (ALPHABET.includes(key)) {
    handleGuess(key);
  }
});

newGameBtn.addEventListener("click", startNewGame);

hintBtn.addEventListener("click", handleHint);

// Page load par: agar koi active game session me hai to use resume karo,
// warna naya game start karo.
(async function init() {
  buildKeyboard();
  hintBtn.textContent = "💡 Hint";
  const res = await fetch("/api/state");
  const state = await res.json();
  if (state.active) {
    categorySelect.value = state.category;
    difficultySelect.value = state.difficulty;
    // Update hint button text to show remaining hints
    const hintsRemaining = state.max_hints - state.hints_used;
    if (hintsRemaining > 0) {
      hintBtn.textContent = `💡 Hint (${hintsRemaining})`;
    }
    renderState(state);
  } else {
    startNewGame();
  }
})();