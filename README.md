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

**17 bugs** were found and fixed — 13 in `app.py`, and 4 in `logic_utils.py`
and the test setup. There was not a single syntax error in the project; every
defect was a logic, state or runtime bug in code that imported and served a
working web page. Full writeup, including reproduction steps for each one, is
in [`reflection.md`](reflection.md).

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
rootdir: /path/to/ai110-module1show-gameglitchinvestigator-starter
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

The example below uses **Easy** so the run is short. The secret is random each
game, so open **Developer Debug Info** if you want to follow along with the
exact numbers shown here (this run had a secret of **12**).

1. **Start the app.** Run `python -m streamlit run app.py` in the project
   folder. Streamlit opens <http://localhost:8501> in your browser.

2. **Pick a difficulty.** In the left sidebar under **Settings**, choose
   **Easy**. The sidebar updates to `Range: 1 to 20` and
   `Attempts allowed: 6`, and the banner above the guess box agrees:
   `Guess a number between 1 and 20. Attempts left: 6`.

3. **Peek at the secret (optional).** Expand **Developer Debug Info** to see
   the secret number, attempts used, score, difficulty and guess history. This
   is how you can confirm the hints are telling the truth.

4. **Make your first guess.** Type `10` into **Enter your guess** and click
   **Submit Guess 🚀**. The secret is 12, so the hint reads **📈 Go HIGHER!**
   and the banner drops to `Attempts left: 5`. The guess box clears itself,
   ready for the next guess.

5. **Follow the hint upward.** Guess `15`. That overshoots, so the hint flips
   to **📉 Go LOWER!** and attempts left falls to `4`. You now know the answer
   is between 11 and 14.

6. **Win.** Guess `12`. Balloons fly and a green banner reads
   `You won! The secret was 12. Final score: 70` — 70 because a win on the
   third attempt scores `100 − 10 × 3`. The guess box is disabled, so you
   cannot keep guessing after the game ends.

7. **Start over.** Click **New Game 🔁**. A new secret is drawn from the *same*
   difficulty's range, and attempts, score and history all reset. Attempts left
   returns to `6` and the game is immediately playable again.

8. **Try losing.** Start a fresh Easy game and guess `1` six times. After the
   sixth, a red banner reads
   `Out of attempts! The secret was 12. Score: 0`, and guessing is locked.
   Click **New Game 🔁** and it recovers straight away.

9. **Confirm bad input is free.** Note the attempts-left number, then submit
   `abc`. You get `'abc' is not a whole number.` and the counter does **not**
   move. Submit `99` on Easy and you get
   `Guess must be between 1 and 20.` — also free. Only a real, in-range guess
   costs an attempt.

10. **Switch difficulty mid-game.** Change the sidebar to **Hard**. Because the
    secret has to come from the new range, a fresh game starts automatically:
    the sidebar reads `Range: 1 to 200` and `Attempts allowed: 8`, and the
    debug panel shows a new secret inside that range.

11. **Turn the hints off.** Untick **Show hint** and guess again. The game still
    tracks attempts and score, but no higher/lower message appears — useful for
    a harder run.

**Screenshot** *(optional)*: <!-- Insert a screenshot of your fixed, winning game here -->

## 🚀 Stretch Features

None attempted. This submission covers the core project only: finding and
fixing the bugs, refactoring the logic into `logic_utils.py`, and getting the
test suite passing.

Because no stretch challenges were attempted, `ai_interactions.md` is
intentionally left blank — it is a stretch-features-only log and is not
required for the core project.
