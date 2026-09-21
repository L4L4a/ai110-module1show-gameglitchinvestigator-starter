# 💭 Reflection: Game Glitch Investigator

## 1. What was broken when you started?

The first run looked deceptively fine: the app loaded, the sidebar rendered, and
the Developer Debug Info panel happily showed the secret number. The problems
only surfaced once I actually tried to win. The hint arrows pointed the wrong
way, the "attempts left" counter started one short, and the very first click of
"New Game" after a win left the app permanently stuck on "You already won."

Two bugs stood out immediately:

- **The hints were backwards.** With the secret visible as 50, guessing 60
  returned "📈 Go HIGHER!".
- **"New Game" was a dead button.** Once the game reached a won or lost state,
  nothing could bring it back. The only recovery was restarting the Streamlit
  server.

Investigating those two led to 17 distinct bugs in total: 13 in `app.py`, and 4
in `logic_utils.py` and the test setup. Notably, the README's hint that "the
secret number changes every time you click Submit" turned out to be a red
herring — the secret was
stored correctly in `st.session_state` and never changed. It only *behaved* as
if it changed, because on alternating attempts it was converted to a string and
compared lexicographically.

**Bug Reproduction Log**

All line numbers refer to the original `app.py` at commit `f651d72`.

| # | Input | Expected Behavior | Actual Behavior | Console Output / Error |
|---|-------|-------------------|-----------------|------------------------|
| 1 | Win, then click "New Game 🔁" | A fresh game starts | Stuck forever on "You already won. Start a new game to play again." | None — silent `st.stop()` at line 145 |
| 2 | Secret 50, guess `9` on the 1st attempt | "Too Low" | "Too High" | None — `TypeError` swallowed by `except` at line 41 |
| 3 | Secret 50, guess `60` | "📉 Go LOWER!" | "📈 Go HIGHER!" | None |
| 4 | Fresh Normal game, before guessing | "Attempts left: 8" | "Attempts left: 7", and the game ends after 7 guesses | None |
| 5 | Guess the secret on the first try | Score 90 | Score 70 | None |
| 6 | Guess `abc` | Error shown, attempt not consumed | Error shown, attempt consumed, `'abc'` pushed into history | None |
| 7 | Secret 50, guess `60` on an even attempt with score 100 | Score 95 | Score 105 — a wrong guess *rewarded* the player | None |
| 8 | Start on Normal (secret 87), switch to Easy | New secret within 1–20 | Secret stays 87 while the sidebar reads "Range: 1 to 20" | None |
| 9 | On Easy, click "New Game 🔁" | Secret within 1–20 | Secret drawn from 1–100, often above 20 | None |
| 10 | Select Easy | Banner reads "between 1 and 20" | Banner reads "between 1 and 100", contradicting the sidebar | None |
| 11 | Compare Hard to Normal | Hard is harder | Hard was 1–50, *narrower* than Normal's 1–100 | None |
| 12 | On Easy, guess `1000` | Rejected as out of range | Accepted as a valid guess | None |
| 13 | Guess `50.9` against secret 50 | Rejected, or treated as not-50 | Truncated to `50` and scored as a **win** | None |
| 14 | `from logic_utils import check_guess` | Working function | `NotImplementedError` | `NotImplementedError: Refactor this function from app.py into logic_utils.py` |
| 15 | `pytest tests/` with correct logic | Tests pass | Fail — compared a tuple to a string | `AssertionError: assert ('Too High', '📈 Go HIGHER!') == 'Too High'` |
| 16 | `cd tests && pytest` | Tests run | Collection error | `ModuleNotFoundError: No module named 'logic_utils'` |
| 17 | `pytest` coverage of `parse_guess` / `update_score` | Covered | No tests existed for either | None |

### Full bug inventory

**Game-breaking**

1. **`app.py:134-138` + `140-145` — "New Game" permanently bricked the app.**
   The handler reset `attempts` and `secret` but never `status`, then called
   `st.rerun()`. On the next run the `status != "playing"` branch hit
   `st.stop()`. *Repro:* win a game, click "New Game", observe it never
   restarts. *Fix:* a single `start_new_game()` helper resets secret, attempts,
   score, status and history, used by both the first load and the button.

2. **`app.py:158-161` — the secret was stringified on even attempts.**
   `secret = str(st.session_state.secret)` forced an `int`/`str` comparison,
   which raised `TypeError`, fell into the `except` branch, and compared the two
   as strings — lexicographically, so `"9" > "50"`. *Repro:* with secret 50,
   guess 9 and be told "Too High". *Fix:* the conversion is gone, and
   `check_guess` coerces both arguments with `int()` so the string path cannot
   return.

3. **`app.py:38, 40` (duplicated at `46, 47`) — the hint messages were
   inverted.** A guess above the secret returned "Go HIGHER!". The outcome label
   was correct, so only the text the player reads lied. *Repro:* secret 50,
   guess 60. *Fix:* swapped the two messages so the arrow and the direction
   agree.

**Off-by-one and state**

4. **`app.py:96` — `attempts` was initialised to `1`, not `0`** (while line 135
   reset it to `0`, so game two behaved differently from game one). This
   understated "Attempts left" by one, cut every difficulty a guess short (7 on
   Normal instead of 8), and flipped the parity of bug 2. *Fix:* starts at `0`
   everywhere, via `start_new_game()`.

5. **`app.py:52` + `171` — win points were off by two increments.**
   `100 - 10 * (attempt_number + 1)` received an already-incremented counter
   that itself started at 1, so a first-guess win scored 70. *Fix:* the formula
   reads a 1-based `attempt_number` directly; a first-guess win is 90.

6. **`app.py:148` vs `150` — invalid input burned an attempt.** `attempts += 1`
   ran before `parse_guess` validated, and line 153 pushed the raw string into
   `history`, mixing `int` and `str`. *Repro:* type `abc`, submit, watch the
   counter drop. *Fix:* parse first; only a real guess increments.

7. **`app.py:57-60` — a wrong guess could raise the score.** "Too High" on an
   even attempt returned `current_score + 5` while "Too Low" was always `-5`.
   *Fix:* both wrong outcomes cost the same 5 points.

**Range and difficulty**

8. **`app.py:92-93` — the secret was never regenerated on a difficulty
   change.** The `if "secret" not in st.session_state` guard ran once, so
   `low`/`high` moved but the number did not. *Fix:* changing difficulty starts
   a fresh game.

9. **`app.py:136` — "New Game" hardcoded `random.randint(1, 100)`,** ignoring
   the difficulty range. *Fix:* draws from the active `low`/`high`.

10. **`app.py:110` — the banner hardcoded "between 1 and 100",** contradicting
    the sidebar on Easy and Hard. *Fix:* interpolates the real range, and is
    rendered through an `st.empty()` placeholder after the guess is processed so
    the attempts count is not a rerun behind.

11. **`app.py:9-10` — "Hard" was easier than "Normal".** Hard was `1, 50`
    against Normal's `1, 100`. *Fix:* see the judgment call in section 6.

12. **`app.py:14-29` — `parse_guess` never range-checked.** `1000` and `-7`
    were valid guesses on Easy. *Fix:* optional `low`/`high` bounds, rejected
    with a message naming the range.

13. **`app.py:22-23` — silent float truncation.** `int(float("50.9"))` gave
    `50`, so a decimal could be scored as a win; meanwhile `1e3` was rejected as
    "not a number", which was inconsistent. *Fix:* decimals are rejected with a
    message explaining why. Input must also match an optional sign followed by
    ASCII digits, because `int()` accepts non-ASCII decimal digits (`"٣"` parsed
    as `3`).

**Refactor and tests**

14. **`logic_utils.py:3, 12, 21, 26` — all four functions were
    `NotImplementedError` stubs** while `app.py:4-65` held working duplicates.
    *Fix:* the logic now lives in `logic_utils.py` and `app.py` imports it,
    keeping only Streamlit wiring.

15. **`tests/test_game_logic.py:6, 11, 16` — assertions compared a tuple to a
    string.** `check_guess` returns `(outcome, message)`, so the tests failed
    even against correct logic. *Fix:* unpack the tuple and assert on the
    outcome.

16. **`tests/` had no `__init__.py`.** Without it pytest prepends `tests/`
    rather than the repo root to `sys.path`, so the import only resolved when
    pytest happened to be invoked from the root. *Fix:* added
    `tests/__init__.py`; `pytest`, `pytest tests/` and running from inside
    `tests/` all work now.

17. **No coverage for `parse_guess`, `update_score`,
    `get_range_for_difficulty`, or the `int`-vs-`str` case** — which is exactly
    why bug 2 survived. *Fix:* 41 tests, including a regression test for every
    bug above.

Two smaller fixes came along the way: the guess box is now a form with
`clear_on_submit`, so it empties after each guess instead of being keyed on
difficulty and wiped whenever the player switched tiers; and win/loss messages
are rendered from `status`, so they survive a rerun instead of vanishing.

---

## 2. How did you use AI as a teammate?

I used **Claude Code (Opus 5)** as the primary tool, driving it from the
terminal in this repository.

**A suggestion that was correct, and how I verified it.** Claude identified the
stringified-secret bug (bug 2) as the real cause of the symptom the README
describes as "the secret number changes every time you click Submit." Its claim
was that the secret never changes at all — the comparison is what breaks,
because `int` vs `str` raises `TypeError`, gets swallowed, and falls back to a
lexicographic string compare. I did not take this on trust. It was verified by
calling the function directly and printing the results:

```
guess   9 vs secret "50" -> ('Too High', ...)   # 9 < 50, so this is wrong
guess 100 vs secret "50" -> ('Too Low',  ...)   # 100 > 50, so this is wrong
guess  50 vs secret "50" -> ('Win',      ...)
```

That output confirmed both the mechanism and that wins still worked, which
explained why the bug had gone unnoticed.

**A suggestion I did not accept as written.** Claude's first version of
`parse_guess` produced the error message "Enter a whole number, not a decimal."
for *any* input that `float()` could parse. That made the message actively
misleading: `1e3` and the Arabic-Indic digit `٣` are not decimals, but both got
told they were. I rejected that phrasing and had it replaced with a check on
whether the text actually contains a `.`, falling back to
`"'{text}' is not a whole number."` otherwise. Verified by re-running the same
inputs and reading each message:

```
'50.9' -> 'Enter a whole number, not a decimal.'
'1e3'  -> "'1e3' is not a whole number."
'٣'    -> "'٣' is not a whole number."
```

The original suggestion was not *wrong* in behaviour — it rejected the right
inputs — but a confusing error message is its own bug when the player is the
one reading it.

---

## 3. Debugging and testing your fixes

I decided a bug was really fixed only when I could demonstrate the old failing
input now producing the right answer, and had a test pinning it there. Reading
the diff was not enough, particularly for the state bugs, where the failure only
appears across multiple Streamlit reruns.

The most useful test was not a pytest case at all. Streamlit's execution model
made the state bugs hard to reason about, so `app.py` was driven against a fake
`streamlit` module that recorded every `st.info`/`st.warning`/`st.error` call and
let each widget's return value be scripted per run. That made an entire play
session assertable:

```
fresh Normal game     -> "Attempts left: 8"
guess 9  (secret 50)  -> "📈 Go HIGHER!"
guess 'abc'           -> attempts unchanged
guess 50              -> status=won, score=90
click New Game        -> status=playing, score/history/attempts reset
8 wrong guesses       -> status=lost
click New Game        -> status=playing          # the bug-1 regression
```

That harness is what proved bug 1 was genuinely fixed, because the failure mode
was "the second rerun stops the script" — something no unit test on the logic
functions would ever catch.

On the pytest side, the run went from **3 failed** to **41 passed**. Two tests
earned their place immediately:
`test_every_difficulty_is_winnable_by_binary_search` computes
`ceil(log2(size + 1))` and asserts the attempt limit is at least that, so the
difficulty tiers cannot drift back into being unwinnable; and
`test_harder_difficulty_means_a_wider_range` asserts the ranges are strictly
increasing, which is the invariant bug 11 violated.

AI helped most in test *design* rather than test *writing* — specifically in
naming the invariant behind bug 11. "Hard should be harder than Normal" is
vague; "the range must widen monotonically **and** stay inside what a binary
search can solve in the attempt limit" is testable, and it immediately exposed
that naively widening Hard to 1–200 while leaving 5 attempts would have made the
tier mathematically impossible.

---

## 4. What did you learn about Streamlit and state?

Streamlit re-runs your entire script from the top on every interaction — every
click, every keystroke committed, every widget change. There is no event handler
that fires "just for the button"; the whole file executes again, and your `if
submit:` block is simply the part of that fresh run which happens to be true.

The way I would explain it to a friend: imagine your program is a recipe that
gets cooked from scratch every single time someone touches anything. Any
ingredient you want to survive between cookings has to be put in the fridge —
that fridge is `st.session_state`. Ordinary local variables are thrown out at
the end of each run.

The subtlety this project drove home is that using `session_state` is not the
same as using it *correctly*. The starter code stored the secret in the fridge
properly, and it still misbehaved, because:

- A partial reset is worse than no reset. "New Game" put a fresh secret in the
  fridge but left the old `status` next to it, and the stale value won. Related
  state has to be reset **together** — which is why a single
  `start_new_game()` function is the actual fix, not four separate assignments.
- Widgets are read *in script order*, so anything printed before the guess is
  processed shows last run's numbers. The "attempts left" banner needed an
  `st.empty()` placeholder filled in after the guess, or it would always lag by
  one.
- `st.rerun()` does not skip the guards above it. Bug 1 was precisely a reset
  that re-entered a script whose own early-exit check then stopped it.

---

## 5. Looking ahead: your developer habits

**The habit I want to keep** is verifying a claim by executing it instead of
reading it. Every bug in the table above was confirmed by running the actual
function or driving the actual app and capturing the output, before any fix was
written. It caught a real error mid-task: the first draft of the input
validation shipped a misleading message for `1e3`, and that only showed up
because the inputs were printed one by one rather than eyeballed.

**What I would do differently** is write the failing test before the fix. I
mostly fixed first and tested after, which works but leaves you trusting that
the test would have failed beforehand. For bug 1 I got this right — the fake
Streamlit harness demonstrated the brick *before* the fix landed — and that was
the bug I was most confident about afterwards. The ordering mattered.

**How this changed how I think about AI-generated code:** the failure mode is
not that it does not run. All 17 bugs were in code that imported, parsed and
served a working web page — there was not a single syntax error in the project.
The code was confidently structured, cleanly formatted, and carried a caption
claiming it was production-ready, while being unwinnable by design. What I take
from this is that "it runs" is the weakest possible evidence, and that
AI-generated code needs the same adversarial reading as a pull request from a
stranger — especially the parts that look too boring to be wrong, like an
`except TypeError` branch or a counter's initial value.

---

## 6. Two judgment calls I reviewed and accepted

Fixing two of the bugs required choosing new behaviour rather than restoring
obviously-correct behaviour. Claude flagged both explicitly instead of quietly
picking, which is what let me review them. I reviewed both and accepted them,
and merged the branch on that basis.

### Hard difficulty tiers

Bug 11 was that Hard (`1, 50`) was narrower — therefore easier — than Normal
(`1, 100`). The minimal fix is to widen Hard's range, but Hard only allowed 5
attempts, and a perfect binary search over 200 numbers needs 8. Widening the
range alone would have replaced "Hard is too easy" with "Hard is impossible,"
which is a strictly worse bug. So the attempt limits moved too:

| Difficulty | Range | Attempts | Binary search needs | Spare guesses |
|------------|-------|----------|---------------------|---------------|
| Easy | 1–20 | 6 | 5 | 1 |
| Normal | 1–100 | 8 | 7 | 1 |
| Hard | 1–200 | 8 | 8 | 0 |

**Why I accepted it:** the ranges now widen monotonically, which is the property
that was actually broken, and every tier stays winnable. Defining Hard as "you
must play perfectly" is a clean, honest difficulty curve rather than an
arbitrary number, and it is enforced by a test rather than by a comment. This
was verified empirically as well as arithmetically: 300 simulated games of
optimal binary search on Hard produced 0 losses.

**What I am accepting as a trade-off:** this changes game balance, not just
correctness. A player used to Hard being a quick 1–50 round will find it
meaningfully harder, and Hard now has no margin for a single wasted guess. If
that proves too punishing, the fix is one number in `ATTEMPT_LIMITS` — and the
winnability test will still hold, because it asserts a floor rather than an
exact value.

### Score floor at 0

Bug 7 was that "Too High" on an even attempt *added* 5 points. Making both wrong
outcomes cost 5 fixes the asymmetry, but it exposed a second oddity that the old
asymmetry had been masking: a player who guesses wrong repeatedly from a score of
0 ends up deep in negative numbers. The original code could reach −20 in a
single lost game. `update_score` now clamps at 0.

**Why I accepted it:** a negative score is not a meaningful state in this game.
Nothing rewards it, nothing displays it usefully, and it reads as a bug to a
player. Clamping is one `max(0, ...)`, it is covered by
`test_score_never_goes_negative`, and it keeps the scoring monotonic in the only
direction that matters — earlier wins score higher.

**What I am accepting as a trade-off:** this is the one change that goes beyond
the literal defect. The reported bug was the asymmetry; the floor is an opinion
about what a score should mean. It is deliberately isolated to a single
expression so it can be dropped without touching anything else, and I would drop
it if the grading rubric wanted penalties to accumulate without limit.
