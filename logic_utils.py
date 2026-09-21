"""Pure game logic for the number guessing game.

This module deliberately imports nothing from Streamlit so that every
function here can be called directly from tests.
"""

import re

# An optional sign followed by ASCII digits. Using this instead of a bare
# int() call keeps non-ASCII decimal digits (e.g. "\u0663") out of the game.
_WHOLE_NUMBER_RE = re.compile(r"^[+-]?[0-9]+$")

# (low, high) inclusive guessing range per difficulty.
#
# The range widens as difficulty increases. "Hard" used to be 1-50, which
# made it *narrower* than "Normal" and therefore easier.
DIFFICULTY_RANGES = {
    "Easy": (1, 20),
    "Normal": (1, 100),
    "Hard": (1, 200),
}

DEFAULT_DIFFICULTY = "Normal"

# Attempts allowed per difficulty. A perfect binary search needs
# ceil(log2(size + 1)) guesses: 5 for Easy, 7 for Normal, 8 for Hard.
# Easy and Normal get one spare guess; Hard requires perfect play.
ATTEMPT_LIMITS = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 8,
}


def get_range_for_difficulty(difficulty: str):
    """Return (low, high) inclusive range for a given difficulty."""
    return DIFFICULTY_RANGES.get(difficulty, DIFFICULTY_RANGES[DEFAULT_DIFFICULTY])


def get_attempt_limit(difficulty: str):
    """Return how many guesses a player gets on a given difficulty."""
    return ATTEMPT_LIMITS.get(difficulty, ATTEMPT_LIMITS[DEFAULT_DIFFICULTY])


def parse_guess(raw: str, low=None, high=None):
    """
    Parse user input into an int guess.

    When low and high are given, the guess must fall inside that
    inclusive range to be accepted.

    Returns: (ok: bool, guess_int: int | None, error_message: str | None)
    """
    if raw is None:
        return False, None, "Enter a guess."

    text = raw.strip()
    if text == "":
        return False, None, "Enter a guess."

    if not _WHOLE_NUMBER_RE.match(text):
        if "." in text:
            return False, None, "Enter a whole number, not a decimal."
        return False, None, f"'{text}' is not a whole number."

    value = int(text)

    if low is not None and value < low:
        return False, None, f"Guess must be between {low} and {high}."

    if high is not None and value > high:
        return False, None, f"Guess must be between {low} and {high}."

    return True, value, None


def check_guess(guess, secret):
    """
    Compare guess to secret and return (outcome, message).

    outcome is one of "Win", "Too High", "Too Low". Both arguments are
    coerced to int so that a stringified secret cannot fall through to a
    lexicographic comparison (where "9" > "50").
    """
    guess = int(guess)
    secret = int(secret)

    if guess == secret:
        return "Win", "🎉 Correct!"

    if guess > secret:
        return "Too High", "📉 Go LOWER!"

    return "Too Low", "📈 Go HIGHER!"


# Awarded for a win on the first guess; each later guess is worth less.
MAX_WIN_POINTS = 100
POINTS_LOST_PER_ATTEMPT = 10
MIN_WIN_POINTS = 10
WRONG_GUESS_PENALTY = 5


def update_score(current_score: int, outcome: str, attempt_number: int):
    """
    Update score based on outcome and attempt number.

    attempt_number is 1-based: 1 means this was the player's first guess.
    """
    if outcome == "Win":
        points = MAX_WIN_POINTS - POINTS_LOST_PER_ATTEMPT * attempt_number
        return current_score + max(MIN_WIN_POINTS, points)

    if outcome in ("Too High", "Too Low"):
        return max(0, current_score - WRONG_GUESS_PENALTY)

    return current_score
