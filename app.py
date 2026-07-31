import streamlit as st
import random

# Page Configuration
st.set_page_config(page_title="Random Word Generator", page_icon="🎲", layout="centered")

st.title("🎲 12-Word Random Generator")
st.write("Enter your word list below (separated by spaces, commas, or newlines).")

# Input area for words
raw_text = st.text_area(
    "Word List (Max 2,048 words):", 
    height=200, 
    placeholder="Enter your words here..."
)

# Process the input text into a list of words
words = [w.strip() for w in raw_text.replace(",", " ").split() if w.strip()]
word_count = len(words)

# Display word counter with limit check
if word_count > 2048:
    st.error(f"You have entered {word_count} words. Please reduce to 2,048 words or fewer.")
else:
    st.info(f"Total Words Detected: **{word_count}** / 2,048")

# Action area
if st.button("Generate 12 Words", type="primary"):
    if word_count < 12:
        st.warning("Please enter at least 12 unique words to generate a selection.")
    else:
        # Secure random sampling without replacement (probability based)
        selected_words = random.sample(words, 12)
        result_text = " ".join(selected_words)
        
        st.success("Successfully generated!")
        
        # Display results in a clean box
        st.subheader("Your 12 Words:")
        st.code(result_text, language=None)
        
        # Streamlit's st.code component includes a built-in copy button in the top right corner.
        # Alternatively, using st.write with code formatting:
        st.caption("Tip: Hover over the box above and click the copy icon on the right to copy to your clipboard.")
