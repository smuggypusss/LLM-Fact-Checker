# LLM-Fact-Checker
🏛️ GovCheck: AI-Powered Government Fact Checker

GovCheck is a production-grade RAG (Retrieval-Augmented Generation) system designed to verify social media claims against official Government of India press releases.

Unlike simple API wrappers, this system employs a Hybrid Search Architecture combining semantic vector retrieval with deterministic fuzzy matching guardrails to ensure high accuracy, low latency, and zero hallucinations on known facts.

🚀 Key Features (Engineering Highlights)

⚡ Hybrid Search Guardrails: Combines FAISS (Vector Search) for semantic understanding with Fuzzy Matching (Levenshtein Distance) to catch exact matches deterministically without wasting LLM tokens.

🏎️ LPU-Speed Inference: Powered by Groq (Llama-3.3-70B) for sub-second reasoning, ensuring a real-time user experience.

📉 Cost-Optimized Embeddings: Uses all-MiniLM-L6-v2 locally (via HuggingFace) to eliminate embedding API costs and reduce network latency.

📡 Live Data Ingestion: Includes an RSS parser (xml_to_csv.py) to fetch real-time updates from the Press Information Bureau (PIB), keeping the knowledge base fresh.

🛡️ Hallucination Thresholding: Implements strict vector distance thresholds to automatically flag vague or unsupported claims as "Unverifiable" before they reach the LLM.

🛠️ Architecture

graph TD
    A[User Input Claim] --> B(Entity Extraction<br/>Spacy NER)
    B --> C{Vector Search<br/>FAISS + MiniLM}
    C -->|Distance > 1.4| D[⛔ Verdict: Unverifiable<br/>(Threshold Guardrail)]
    C -->|Distance < 1.4| E{Hybrid Guardrail<br/>Fuzzy Match}
    E -->|Similarity > 70%| F[✅ Verdict: True<br/>(Deterministic Match)]
    E -->|No Exact Match| G[🧠 LLM Reasoning<br/>Groq Llama-3-70B]
    G --> H[Final JSON Verdict]


📦 Installation

Clone the repository:

git clone [https://github.com/smuggypusss/LLM-Fact-Checker.git](https://github.com/smuggypusss/LLM-Fact-Checker.git)
cd govcheck-fact-checker


Install dependencies:

pip install -r requirements.txt


Download Spacy Model:

python -m spacy download en_core_web_sm


🏃‍♂️ Usage Guide

1. Data Ingestion (Optional)

To fetch the latest government press releases from the live PIB RSS feed:

python xml_to_csv.py


This generates a fresh facts.csv file.

2. Run the Application

Launch the Streamlit frontend:

streamlit run app.py


3. Verify a Claim

Enter your Groq API Key in the sidebar.

Upload the facts.csv file (provided in repo or generated above).

Click "Embed & Index".

Enter a claim (e.g., "Union Home Minister Amit Shah paid respects to Guru Tegh Bahadur Ji").

View the Verdict, Confidence Score, and Source Evidence.

📂 Project Structure

File

Description

core.py

The Brain. Contains the FactChecker class, FAISS vector logic, Hybrid Guardrails, and Groq integration. Decoupled from UI.

app.py

The Frontend. Streamlit UI that handles user inputs, API key management, and visualizes the RAG results.

xml_to_csv.py

ETL Pipeline. Parses XML RSS feeds from government websites into a clean CSV format for ingestion.

facts.csv

Sample database of trusted government facts.

🧠 Engineering Decisions (Why I built it this way)

1. Why Local Embeddings (all-MiniLM-L6-v2)?

Instead of using OpenAI's embedding API, I used a local HuggingFace model.

Reason: Fact-checking requires low latency. Running embeddings on the CPU eliminates the network round-trip time. It also reduces operational costs to zero for the retrieval layer.

2. Why Hybrid Search (Fuzzy + Vector)?

Vector search is great for concepts, but bad at exact numbers. If a claim says "₹500 subsidy" and the fact says "₹500 subsidy," vector search might return a distance score of 0.2.

Reason: I added a SequenceMatcher guardrail. If text similarity is >70%, we force a True verdict immediately. This makes the system deterministic for known facts and "bulletproof" against LLM variability.

3. Why Groq?

Reason: Fact-checking is a real-time activity. Waiting 5+ seconds for GPT-4 breaks the user flow. Groq's LPU provides near-instant inference, making the tool feel like a database query rather than a generative AI task.

