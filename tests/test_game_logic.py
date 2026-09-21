import math

import pytest

from logic_utils import (
    ATTEMPT_LIMITS,
    DIFFICULTY_RANGES,
    check_guess,
    get_attempt_limit,
    get_range_for_difficulty,
    parse_guess,
    update_score,
)


# --- check_guess -----------------------------------------------------------
#
# check_guess returns a (outcome, message) tuple, so the outcome has to be
# unpacked before it is compared. Asserting on the whole return value is
# what made these tests fail even against correct logic.

def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    outcome, message = check_guess(50, 50)
    assert outcome == "Win"
    assert "Correct" in message


def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    outcome, message = check_guess(60, 50)
    assert outcome == "Too High"


def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    outcome, message = check_guess(40, 50)
    assert outcome == "Too Low"


def test_too_high_tells_the_player_to_go_lower():
    # The regression: the outcome was right but the message was inverted.
    _, message = check_guess(60, 50)
    assert "LOWER" in message


def test_too_low_tells_the_player_to_go_higher():
    _, message = check_guess(40, 50)
    assert "HIGHER" in message


@pytest.mark.parametrize(
    "guess, expected",
    [(9, "Too Low"), (40, "Too Low"), (50, "Win"), (60, "Too High"), (100, "Too High")],
)
def test_string_secret_is_compared_numerically(guess, expected):
    # A stringified secret used to be compared lexicographically, so "9"
    # read as greater than "50" and 9 was reported as Too High.
    outcome, _ = check_guess(guess, "50")
    assert outcome == expected


# --- parse_guess -----------------------------------------------------------

@pytest.mark.parametrize("raw, expected", [("42", 42), (" 42 ", 42), ("+42", 42)])
def test_parse_guess_accepts_whole_numbers(raw, expected):
    ok, value, error = parse_guess(raw)
    assert (ok, value, error) == (True, expected, None)


@pytest.mark.parametrize("raw", ["", "   ", None])
def test_parse_guess_requires_input(raw):
    ok, value, error = parse_guess(raw)
    assert not ok
    assert error == "Enter a guess."


@pytest.mark.parametrize("raw", ["abc", "1e3", "٣", "0x10", "--5"])
def test_parse_guess_rejects_non_numbers(raw):
    ok, value, error = parse_guess(raw)
    assert not ok
    assert value is None


def test_parse_guess_rejects_decimals_instead_of_truncating():
    # "50.9" used to parse as 50 via int(float(raw)) and could win.
    ok, value, error = parse_guess("50.9")
    assert not ok
    assert value is None


@pytest.mark.parametrize("raw", ["0", "21", "-7", "1000"])
def test_parse_guess_rejects_out_of_range(raw):
    ok, value, error = parse_guess(raw, 1, 20)
    assert not ok
    assert error == "Guess must be between 1 and 20."


@pytest.mark.parametrize("raw", ["1", "20", "13"])
def test_parse_guess_accepts_bounds_inclusively(raw):
    ok, value, error = parse_guess(raw, 1, 20)
    assert ok
    assert value == int(raw)


# --- update_score ----------------------------------------------------------

def test_first_guess_win_scores_ninety():
    # Was 70: the formula added one to an already-incremented counter.
    assert update_score(0, "Win", 1) == 90


def test_win_points_shrink_with_each_attempt():
    scores = [update_score(0, "Win", n) for n in range(1, 9)]
    assert scores == [90, 80, 70, 60, 50, 40, 30, 20]


def test_win_points_never_fall_below_ten():
    assert update_score(0, "Win", 50) == 10


@pytest.mark.parametrize("outcome", ["Too High", "Too Low"])
def test_wrong_guesses_cost_the_same(outcome):
    # "Too High" on an even attempt used to *add* 5 points.
    assert update_score(100, outcome, 2) == 95
    assert update_score(100, outcome, 3) == 95


def test_score_never_goes_negative():
    assert update_score(3, "Too Low", 1) == 0


def test_unknown_outcome_leaves_score_alone():
    assert update_score(42, "Sideways", 1) == 42


# --- difficulty ------------------------------------------------------------

def test_harder_difficulty_means_a_wider_range():
    # "Hard" was 1-50, narrower than "Normal" at 1-100.
    sizes = [
        DIFFICULTY_RANGES[d][1] - DIFFICULTY_RANGES[d][0]
        for d in ("Easy", "Normal", "Hard")
    ]
    assert sizes == sorted(sizes)
    assert len(set(sizes)) == len(sizes)


def test_unknown_difficulty_falls_back_to_normal():
    assert get_range_for_difficulty("Bogus") == DIFFICULTY_RANGES["Normal"]
    assert get_attempt_limit("Bogus") == ATTEMPT_LIMITS["Normal"]


@pytest.mark.parametrize("difficulty", ["Easy", "Normal", "Hard"])
def test_every_difficulty_is_winnable_by_binary_search(difficulty):
    low, high = get_range_for_difficulty(difficulty)
    needed = math.ceil(math.log2(high - low + 2))
    assert get_attempt_limit(difficulty) >= needed
