# 🎮 Game Glitch Investigator: The Impossible Guesser

A number guessing game built with [Streamlit](https://streamlit.io/). You pick a
difficulty, the app draws a secret number in that range, and you get a limited
number of guesses with a higher/lower hint after each one. Points are awarded
for winning — the earlier you win, the more you score.

## 🚨 The Situation

The original version of this game was AI-generated and shipped with a caption
claiming it was production-ready. It was unplayable:

- You could not win reliably — the hints pointed the wrong way.
- "New Game" bricked the app permanently after the first win or loss.
- The secret number appeared to change between guesses.
- `logic_utils.py` was four `NotImplementedError` stubs, and all three tests
  failed.

**17 bugs** were found and fixed — 13 in `app.py`, and 4 in
`logic_utils.py` and the test setup. There
was not a single syntax error in the project; every defect was a logic, state or
runtime bug in code that imported and served a working web page. Full writeup,
including reproduction steps for each one, is in
[`reflection.md`](reflection.md).

## 🛠️ Setup

Requires Python 3.9 or newer.

```bash
pip install -r requirements.txt
```

## ▶️ Running the app

```bash
python -m streamlit run app.py
```

Streamlit serves the app at <http://localhost:8501> and opens it in your
browser. Press `Ctrl+C` in the terminal to stop it.

## 🕹️ How to play

1. Pick a **Difficulty** in the sidebar. It shows the number range and how many
   guesses you get.
2. Type a whole number into **Enter your guess** and press **Submit Guess 🚀**.
3. After each wrong guess you get a hint — **📈 Go HIGHER!** or
   **📉 Go LOWER!** — unless you untick **Show hint**.
4. Win before your attempts run out. Your score depends on how few guesses you
   needed.
5. Click **New Game 🔁** at any time to start over with a new secret number.

Expand **Developer Debug Info** to see the secret, the attempts used, the score
and your guess history — useful for verifying the game behaves correctly.

### Difficulty tiers

Each tier is guaranteed winnable: the attempt limit is never fewer than the
`ceil(log2(size + 1))` guesses a perfect binary search requires. Hard requires
playing perfectly.

| Difficulty | Range | Attempts | Binary search needs |
|------------|-------|----------|---------------------|
| Easy | 1–20 | 6 | 5 |
| Normal | 1–100 | 8 | 7 |
| Hard | 1–200 | 8 | 8 |

### Scoring

| Event | Effect |
|-------|--------|
| Win | `100 − 10 × attempt_number`, minimum 10 (so a first-guess win scores 90) |
| Wrong guess | −5, and the score never drops below 0 |
| Invalid input | No change, and it does not consume an attempt |

## 📁 Project structure

```
app.py                     Streamlit UI and session-state handling only
logic_utils.py             Pure game logic — imports nothing from Streamlit
tests/test_game_logic.py   41 tests covering the logic and every fixed bug
requirements.txt           streamlit, altair, pytest
reflection.md              All 17 bugs: repro steps, fixes, and design notes
```

The logic lives in `logic_utils.py` and deliberately has no Streamlit import, so
every function can be called directly from tests without spinning up a server.
`app.py` holds the UI wiring and the `session_state` lifecycle.

## 🧪 Test Results

```bash
python3 -m pytest
```

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0
rootdir: /Users/elviskenneth/Downloads/ai110-module1show-gameglitchinvestigator-starter
collected 41 items

tests/test_game_logic.py .........................................       [100%]

============================== 41 passed in 0.03s ==============================
```

Tests run from the repo root, from inside `tests/`, or with an explicit path —
`tests/__init__.py` ensures the `logic_utils` import resolves in all three
cases.

Coverage includes a regression test for each of the 17 bugs, plus two invariant
tests that keep the difficulty tiers honest:
`test_harder_difficulty_means_a_wider_range` asserts the ranges widen
monotonically, and `test_every_difficulty_is_winnable_by_binary_search` asserts
no tier can be made mathematically impossible.

## 📸 Demo Walkthrough

Describe your fixed game in numbered steps so a reader can follow along without
watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot** *(optional)*: <!-- Insert a screenshot of your fixed, winning game here -->

## 🚀 Stretch Features

- [ ] [If you choose to complete Challenge 4, describe the Enhanced UI changes here — a screenshot is optional]
