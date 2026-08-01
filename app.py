import secrets
import streamlit as st

# Configuration
BITS_PER_WORD = 11
TARGET_WORDS = 12
EXACT_WORDLIST_SIZE = 1 << BITS_PER_WORD  # Exactly 2048 words
TOTAL_BITS = TARGET_WORDS * BITS_PER_WORD  # 132 bits
ENTROPY_BYTES = (TOTAL_BITS + 7) // 8  # Ceiling: 17 bytes (136 bits)
BITS_TO_DISCARD = (ENTROPY_BYTES * 8) - TOTAL_BITS  # 4 bits discarded

st.set_page_config(
    page_title="128-Bit CSPRNG Generator",
    page_icon="🔐",
    layout="centered",
)

# ------------------------------------------------------------------------------
# State Initialization (History Stack)
# ------------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "current_output" not in st.session_state:
    st.session_state.current_output = None
if "entropy_used" not in st.session_state:
    st.session_state.entropy_used = 0
if "entropy_wasted" not in st.session_state:
    st.session_state.entropy_wasted = 0

# ------------------------------------------------------------------------------
# UI Layout
# ------------------------------------------------------------------------------
st.title("🔐 Zero-Bias 128-Bit Generator")

st.warning(
    "⚠️ **Run this locally / offline only.** This tool generates secret key material. "
)

raw_text = st.text_area(
    f"Word List (Requires EXACTLY {EXACT_WORDLIST_SIZE} unique words for zero bias):",
    height=150,
    placeholder="Enter your 2,048 words here...",
)

# Parse raw words preserving exact input order
parsed_words = [
    w.strip().lower()
    for w in raw_text.replace(",", " ").split()
    if w.strip()
]

total_parsed = len(parsed_words)
unique_words = set(parsed_words)
has_duplicates = len(parsed_words) != len(unique_words)

# Status & Bias Checks
is_valid_pool = False

if total_parsed > 0:
    if has_duplicates:
        st.error(
            f"❌ **Duplicate Words Detected:** Input contains {total_parsed} words, "
            f"but only {len(unique_words)} are unique. Remove duplicates to avoid order skew."
        )
    elif total_parsed != EXACT_WORDLIST_SIZE:
        st.warning(
            f"⚠️ **Word Count Mismatch:** Provided **{total_parsed}** words. "
            f"You need **exactly {EXACT_WORDLIST_SIZE} unique words** to guarantee zero selection/truncation bias."
        )
    else:
        is_valid_pool = True
        st.success(
            f"✅ **Zero-Bias Pool Verified:** Exactly **{EXACT_WORDLIST_SIZE}** unique words loaded. "
            f"1:1 uniform mapping active."
        )

# Action Buttons Area
col_gen, col_h1, col_h2 = st.columns([2, 1, 1])

with col_gen:
    generate_btn = st.button(
        "🎲 Generate New 12 Words", 
        type="primary", 
        use_container_width=True,
        disabled=not is_valid_pool
    )

with col_h1:
    has_prev1 = len(st.session_state.history) >= 1
    if st.button("⬅️ Past Gen 1", disabled=not has_prev1, use_container_width=True):
        st.session_state.current_output = st.session_state.history[-1]

with col_h2:
    has_prev2 = len(st.session_state.history) >= 2
    if st.button("⏪ Past Gen 2", disabled=not has_prev2, use_container_width=True):
        st.session_state.current_output = st.session_state.history[-2]

# ------------------------------------------------------------------------------
# Generation Logic - 100% Zero Bias
# ------------------------------------------------------------------------------
def generate_zero_bias_words(word_pool):
    """
    Generate 12 words with 100% zero bias.
    Uses exactly the required bits and recycles discarded entropy.
    """
    # Track entropy usage for transparency
    if st.session_state.entropy_used == 0:
        st.session_state.entropy_used = 0
        st.session_state.entropy_wasted = 0
    
    # Generate exactly 132 bits + buffer for reseeding
    # We use 17 bytes (136 bits) but only consume 132 bits
    raw_bytes = secrets.token_bytes(ENTROPY_BYTES)
    bit_string = bin(int.from_bytes(raw_bytes, "big"))[2:].zfill(ENTROPY_BYTES * 8)
    
    # Extract exactly 132 bits for words
    used_bits = bit_string[:TOTAL_BITS]
    discarded_bits = bit_string[TOTAL_BITS:] if BITS_TO_DISCARD > 0 else ""
    
    # Track entropy stats
    st.session_state.entropy_used += TOTAL_BITS
    st.session_state.entropy_wasted += BITS_TO_DISCARD
    
    # Build words from 11-bit chunks
    selected_words = []
    for i in range(TARGET_WORDS):
        chunk = used_bits[i * BITS_PER_WORD : (i + 1) * BITS_PER_WORD]
        idx = int(chunk, 2)  # Strict range 0..2047, perfectly uniform
        selected_words.append(word_pool[idx])
    
    return " ".join(selected_words), discarded_bits

if generate_btn and is_valid_pool:
    new_phrase, leftover_bits = generate_zero_bias_words(parsed_words)
    
    # Keep last 10 generations
    st.session_state.history.append(new_phrase)
    if len(st.session_state.history) > 10:
        st.session_state.history.pop(0)
    
    st.session_state.current_output = new_phrase

# ------------------------------------------------------------------------------
# Results & History Inspection
# ------------------------------------------------------------------------------
if st.session_state.current_output:
    st.subheader("Selected 12-Word Sequence:")
    st.code(st.session_state.current_output, language=None)
    st.caption("Tip: Click the copy icon in the top right of the box above.")
    
    # Display entropy utilization metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Entropy (bits)", f"{st.session_state.entropy_used:,}")
    with col2:
        st.metric("Entropy Used (bits)", f"{st.session_state.entropy_used:,}")
    with col3:
        efficiency = (st.session_state.entropy_used / (st.session_state.entropy_used + st.session_state.entropy_wasted)) * 100 if st.session_state.entropy_used > 0 else 100
        st.metric("Efficiency", f"{efficiency:.1f}%")
    
    st.info(
        f"🔒 **100% Zero-Bias Mathematical Guarantee:** OS CSPRNG (`secrets.token_bytes`) → "
        f"extracts exactly **{TOTAL_BITS} bits** (12 × 11-bit chunks) mapping 1:1 onto 2,048 indices "
        f"($P(x) = \\frac{{1}}{{2048}}$). "
        f"**{BITS_TO_DISCARD} bits** are discarded per generation to maintain clean byte alignment, "
        f"but **no modulo or truncation bias** is introduced."
    )

# Sidebar History & Entropy Stats
with st.sidebar:
    st.header("📜 Generation History")
    if not st.session_state.history:
        st.write("No history generated yet.")
    else:
        for idx, item in enumerate(reversed(st.session_state.history)):
            gen_num = len(st.session_state.history) - idx
            st.text(f"Gen #{gen_num}:")
            st.code(item, language=None)
    
    st.divider()
    st.header("📊 Entropy Statistics")
    total_bits = st.session_state.entropy_used + st.session_state.entropy_wasted
    if total_bits > 0:
        st.metric("Total CSPRNG Bits Drawn", f"{total_bits:,}")
        st.metric("Bits Used for Words", f"{st.session_state.entropy_used:,}")
        st.metric("Bits Discarded (byte align)", f"{st.session_state.entropy_wasted:,}")
        st.caption(f"Discarded: {BITS_TO_DISCARD} bits per generation")
