import math
import os
import streamlit as st

# Configuration
ENTROPY_BITS = 128
ENTROPY_BYTES = 17  # 136 bits needed for 12 * 11-bit chunks
TARGET_WORDS = 12

st.set_page_config(
    page_title="128-Bit CSPRNG Generator", page_icon="🔐", layout="centered"
)

# ------------------------------------------------------------------------------
# State Initialization (History Stack)
# ------------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []  # Holds past word outputs

if "current_output" not in st.session_state:
    st.session_state.current_output = None

# ------------------------------------------------------------------------------
# UI Layout
# ------------------------------------------------------------------------------
st.title("🔐 128-Bit Generator with History")

raw_text = st.text_area(
    "Word List (Requires 2,048 unique words for full 128-bit security):",
    height=150,
    placeholder="Enter your words here...",
)

words = list(
    dict.fromkeys(
        w.strip().lower()
        for w in raw_text.replace(",", " ").split()
        if w.strip()
    )
)
word_count = len(words)

# Status Checks
if word_count > 0:
    if word_count < 2048:
        st.warning(
            f"Current pool: **{word_count}** words. You need **2,048 unique words** for true 128-bit security."
        )
    else:
        st.success(f"Pool size verified: **{word_count}** words (≥ 11 bits/word).")

# Action Buttons Area
col_gen, col_h1, col_h2 = st.columns([2, 1, 1])

with col_gen:
    generate_btn = st.button("🎲 Generate New 12 Words", type="primary", use_container_width=True)

# Button to load 1 generation back
with col_h1:
    has_prev1 = len(st.session_state.history) >= 1
    if st.button("⬅️ Past Gen 1", disabled=not has_prev1, use_container_width=True):
        st.session_state.current_output = st.session_state.history[-1]

# Button to load 2 generations back
with col_h2:
    has_prev2 = len(st.session_state.history) >= 2
    if st.button("⏪ Past Gen 2", disabled=not has_prev2, use_container_width=True):
        st.session_state.current_output = st.session_state.history[-2]

# ------------------------------------------------------------------------------
# Generation Logic
# ------------------------------------------------------------------------------
if generate_btn:
    if word_count < 12:
        st.error("Please enter at least 12 words.")
    else:
        # Hardware entropy draw
        raw_bytes = os.urandom(ENTROPY_BYTES)
        bit_string = bin(int.from_bytes(raw_bytes, byteorder="big"))[2:].zfill(
            ENTROPY_BYTES * 8
        )

        selected_words = []
        for i in range(TARGET_WORDS):
            # 11-bit slicing (for 2048 pool mapping)
            chunk = bit_string[i * 11 : (i + 1) * 11]
            idx = int(chunk, 2) % word_count
            selected_words.append(words[idx])

        new_phrase = " ".join(selected_words)

        # Update Session History (Keep last 10 generations in memory)
        st.session_state.history.append(new_phrase)
        if len(st.session_state.history) > 10:
            st.session_state.history.pop(0)

        # Set current active output
        st.session_state.current_output = new_phrase

# ------------------------------------------------------------------------------
# Results & History Inspection
# ------------------------------------------------------------------------------
if st.session_state.current_output:
    st.subheader("Selected 12-Word Sequence:")
    st.code(st.session_state.current_output, language=None)
    st.caption("Tip: Click the copy icon in the top right of the box above.")

# Sidebar History Log
with st.sidebar:
    st.header("📜 Generation History")
    if not st.session_state.history:
        st.write("No history generated yet.")
    else:
        for idx, item in enumerate(reversed(st.session_state.history)):
            gen_num = len(st.session_state.history) - idx
            st.text(f"Gen #{gen_num}:")
            st.code(item, language=None)
