import random

import streamlit as st

from logic_utils import (
    check_guess,
    get_attempt_limit,
    get_range_for_difficulty,
    parse_guess,
    update_score,
)

st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

low, high = get_range_for_difficulty(difficulty)
attempt_limit = get_attempt_limit(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")


def start_new_game():
    """Reset every piece of game state for the current difficulty."""
    st.session_state.difficulty = difficulty
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []


if "secret" not in st.session_state:
    start_new_game()

# The secret is drawn from the difficulty's range, so changing difficulty
# has to deal a new number or the old one may sit outside the new range.
if st.session_state.difficulty != difficulty:
    start_new_game()

playing = st.session_state.status == "playing"

st.subheader("Make a guess")

# Filled in after the guess is processed so the count is not a rerun behind.
info_slot = st.empty()

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts used:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

with st.form("guess_form", clear_on_submit=True):
    raw_guess = st.text_input("Enter your guess:", disabled=not playing)
    submit = st.form_submit_button("Submit Guess 🚀", disabled=not playing)

col1, col2 = st.columns(2)
with col1:
    new_game = st.button("New Game 🔁")
with col2:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    start_new_game()
    st.rerun()

if playing and submit:
    ok, guess_int, err = parse_guess(raw_guess, low, high)

    if not ok:
        # A guess that never parsed is not an attempt, so the counter and
        # the history stay untouched.
        st.error(err)
    else:
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        outcome, message = check_guess(guess_int, st.session_state.secret)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.session_state.status = "won"
            st.balloons()
        elif st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"
        elif show_hint:
            st.warning(message)

attempts_left = max(0, attempt_limit - st.session_state.attempts)
info_slot.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempts_left}"
)

if st.session_state.status == "won":
    st.success(
        f"You won! The secret was {st.session_state.secret}. "
        f"Final score: {st.session_state.score}"
    )
elif st.session_state.status == "lost":
    st.error(
        f"Out of attempts! "
        f"The secret was {st.session_state.secret}. "
        f"Score: {st.session_state.score}"
    )

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
