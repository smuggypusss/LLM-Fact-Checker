import streamlit as st
from core import checker
import pandas as pd

st.set_page_config(page_title="GovCheck: AI Fact Verifier", layout="wide")

st.title("🏛️ LLM-Powered Fact Checker")

# Sidebar
with st.sidebar:
    st.header("Settings")
    # API Key Input
    api_key = st.secrets['GROQ_API_KEY']


    st.divider()
    st.header("Knowledge Base")
    uploaded_file = st.file_uploader("Upload Facts (CSV)", type="csv")

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if st.button("Embed & Index"):
            with st.spinner("Embedding data..."):
                checker.create_vector_db(df)  # Passing the DataFrame now
            st.success(f"Indexed {len(df)} facts!")

# Main Area
claim_input = st.text_area("Enter a Claim:", height=100,
                           value="Union Home Minister Amit Shah paid respects to Guru Tegh Bahadur Ji in Delhi.")

if st.button("Verify Claim"):
    if not checker.vector_store:
        st.error("⚠️ Please upload and index the Knowledge Base first!")
    elif not api_key:
        st.error("⚠️ Please enter your Groq API Key in the sidebar!")
    else:
        with st.spinner("Analyzing with Llama 3 70B..."):
            # Extraction
            ext = checker.extract_entities_and_claim(claim_input)
            st.write(f"**Entities Detected:** {ext['entities']}")

            # Verification
            result = checker.verify_claim(claim_input)

            # Display
            verdict = result.get("verdict", "Error")
            if verdict == "True":
                st.success("✅ TRUE")
            elif verdict == "False":
                st.error("❌ FALSE")
            elif verdict == "Unverifiable":
                st.warning("🤷‍♂️ UNVERIFIABLE")
            else:
                st.error("⚠️ ERROR")

            st.write(f"**Reasoning:** {result.get('reasoning')}")

            with st.expander("View Evidence & Sources"):
                for i, ev in enumerate(result.get("evidence", [])):
                    st.info(f"Evidence: {ev}")
                for src in result.get("sources", []):
                    st.caption(f"Source: {src}")