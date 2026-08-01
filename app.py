import os
import secrets
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Random Word Generator (Entropy Enabled)", page_icon="🎲", layout="centered"
)

st.title("🎲 12-Word Random Generator")
st.write("Enter your word list below (separated by spaces, commas, or newlines).")

# Input area for words
raw_text = st.text_area(
    "Word List (Max 2,048 words):",
    height=200,
    placeholder="Enter your words here...",
)

# Process input into unique words (preserving original order)
words = list(dict.fromkeys(w.strip() for w in raw_text.replace(",", " ").split() if w.strip()))
word_count = len(words)

# Display word counter with limit check
if word_count > 2048:
    st.error(
        f"You have entered {word_count} unique words. Please reduce to 2,048 words or fewer."
    )
elif word_count > 0:
    st.info(f"Unique Words Detected: **{word_count}** / 2,048")

# Action area
if st.button("Generate 12 Words", type="primary"):
    if word_count < 12:
        st.warning(
            f"Please enter at least 12 unique words (currently have {word_count})."
        )
    else:
        # Machine-level hardware entropy sampling
        # os.urandom pulls directly from system kernel entropy pool (/dev/urandom / CryptGenRandom)
        sys_rand = secrets.SystemRandom()
        selected_words = sys_rand.sample(words, 12)
        result_text = " ".join(selected_words)

        st.success("Successfully generated using System Entropy!")

        # Display results in a clean box
        st.subheader("Your 12 Words:")
        st.code(result_text, language=None)
        
        # Display Entropy Level & Metrics
        st.divider()
        st.subheader("🛡️ Entropy Analysis")
        
        # Bits of entropy per selection: log2(N! / (N-k)!)
        import math
        possible_combinations = math.comb(word_count, 12) * math.factorial(12)
        entropy_bits = math.log2(possible_combinations)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Entropy Level", value=f"{entropy_bits:.2f} bits")
        with col2:
            st.metric(label="Entropy Source", value="Kernel (/dev/urandom)")
            
        st.caption(
            "Note: Selection utilizes hardware interrupt jitter & OS kernel entropy pools via `os.urandom()`."
        )
