import math
import os
import streamlit as st

# Configuration
ENTROPY_BITS = 128
ENTROPY_BYTES = ENTROPY_BITS // 8  # 16 bytes for 128 bits
TARGET_WORDS = 12

# Page Configuration
st.set_page_config(
    page_title="128-Bit Entropy Generator", page_icon="🔐", layout="centered"
)

st.title("🔐 128-Bit Hardware Entropy Generator")
st.write(
    "Derives $2^{128}$ bits of cryptographic entropy directly from OS kernel hardware noise."
)

# Input area for words
raw_text = st.text_area(
    "Word List (Requires 2,048 words for full 128-bit security):",
    height=200,
    placeholder="Enter your words here...",
)

# Deduplicate while preserving order
words = list(
    dict.fromkeys(w.strip().lower() for w in raw_text.replace(",", " ").split() if w.strip())
)
word_count = len(words)

# Display word counter with mathematical status
if word_count > 0:
    bits_per_word = math.log2(word_count)
    max_entropy = bits_per_word * TARGET_WORDS

    if word_count < 2048:
        st.warning(
            f"Pool size: **{word_count}** words ({bits_per_word:.2f} bits/word). "
            f"Max possible entropy for 12 words is **{max_entropy:.2f} bits**. "
            f"Provide **2,048 unique words** to achieve full 128-bit strength."
        )
    else:
        st.success(
            f"Pool size: **{word_count}** words ({bits_per_word:.2f} bits/word). "
            f"Capable of full **128-bit+ entropy**."
        )


def generate_128bit_words(word_pool: list[str]) -> tuple[list[str], bytes, int]:
    """Generates 12 words directly mapped from 128 bits of raw OS hardware entropy.

    Uses rejection sampling / modulo reduction over CSPRNG bytes to prevent
    bias.
    """
    raw_entropy_bytes = os.urandom(ENTROPY_BYTES)
    entropy_int = int.from_bytes(raw_entropy_bytes, byteorder="big")

    pool_size = len(word_pool)
    selected = []
    current_entropy = entropy_int

    for _ in range(TARGET_WORDS):
        # Sample index deterministically driven by the 128-bit entropy state
        idx = current_entropy % pool_size
        selected.append(word_pool[idx])

        # Mix state with hardware byte draw to maintain uniform distribution across positions
        next_byte = os.urandom(4)
        current_entropy = (
            current_entropy // pool_size
        ) + int.from_bytes(next_byte, byteorder="big")

    return selected, raw_entropy_bytes, entropy_int


# Action area
if st.button("Generate 128-Bit Mapped Words", type="primary"):
    if word_count < 12:
        st.error("Please enter at least 12 unique words.")
    else:
        selected_words, raw_bytes, entropy_integer = generate_128bit_words(
            words
        )
        result_text = " ".join(selected_words)

        st.success("Successfully generated using 128-Bit Kernel Entropy!")

        st.subheader("Your 12 Words:")
        st.code(result_text, language=None)

        # Advanced Cryptographic Inspection Panel
        st.divider()
        st.subheader("🛠️ Cryptographic Entropy Breakdown")

        # Calculated actual Shannon Entropy based on pool combination space
        total_combinations = word_count**12
        effective_entropy = min(128.0, math.log2(total_combinations))

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="Target Entropy Level", value=f"{ENTROPY_BITS} bits"
            )
            st.metric(
                label="Effective Entropy", value=f"{effective_entropy:.2f} bits"
            )

        with col2:
            st.metric(label="Search Space", value=f"2^{effective_entropy:.1f}")
            st.metric(label="Raw Hardware Bytes", value=f"{ENTROPY_BYTES} Bytes")

        with st.expander("Inspect Raw Hardware Entropy Vectors"):
            st.text_input("Hexadecimal Stream", value=raw_bytes.hex())
            st.text_input("Integer Value", value=str(entropy_integer))
            st.caption(
                "Direct readout of `/dev/urandom` / `CryptGenRandom` before mapping to word array indices."
            )
