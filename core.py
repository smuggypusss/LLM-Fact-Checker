import os
import json
import spacy
import pandas as pd
from difflib import SequenceMatcher
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from groq import Groq
import streamlit as st

# Load Spacy
try:
    nlp = spacy.load("en_core_web_sm")
except:
    os.system("python -m spacy download en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")


class FactChecker:
    def __init__(self):
        print("Loading Embedding Model...")
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = None
        self.api_key = st.secrets['GROQ_API_KEY']

    def set_api_key(self, key):
        self.api_key = key

    def extract_entities_and_claim(self, text):
        doc = nlp(text)
        entities = [ent.text for ent in doc.ents]
        return {"original_text": text, "entities": entities}

    def create_vector_db(self, data):
        # Handle DataFrame or List
        if isinstance(data, pd.DataFrame):
            texts = data['text'].tolist()
            sources = data['source'].fillna("Unknown").tolist()
            metadatas = [{'source': src} for src in sources]
        else:
            texts = data
            metadatas = [{'source': 'User Upload'} for _ in data]

        self.vector_store = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
        return True

    def check_fuzzy_match(self, claim, evidence_list):

        for evidence in evidence_list:
            similarity = SequenceMatcher(None, claim.lower(), evidence.lower()).ratio()
            # If > 70% similar or contained within
            if similarity > 0.7 or claim.lower() in evidence.lower():
                return True, evidence
        return False, None

    def call_groq_llm(self, prompt):
        if not self.api_key:
            return json.dumps({"verdict": "Error", "reasoning": "Groq API Key is missing."})

        client = Groq(api_key=self.api_key)

        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a JSON-only API. Return strict JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}  # Force JSON mode
            )
            return completion.choices[0].message.content
        except Exception as e:
            return json.dumps({"verdict": "Error", "reasoning": str(e)})

    def verify_claim(self, claim_text):
        if not self.vector_store:
            return {"error": "Knowledge base not loaded."}

        # 1. RETRIEVAL
        docs_and_scores = self.vector_store.similarity_search_with_score(claim_text, k=3)

        relevant_docs = []
        evidence_sources = []

        for doc, score in docs_and_scores:
            if score < 1.4:
                relevant_docs.append(doc.page_content)
                evidence_sources.append(doc.metadata.get('source', 'Unknown'))

        if not relevant_docs:
            return {
                "verdict": "Unverifiable",
                "evidence": [],
                "reasoning": "No relevant records found in the database."
            }

        # 2. GUARDRAIL CHECK
        is_match, matched_fact = self.check_fuzzy_match(claim_text, relevant_docs)
        if is_match:
            return {
                "verdict": "True",
                "evidence": [matched_fact],
                "sources": list(set(evidence_sources)),
                "reasoning": "Exact match found in official government records."
            }

        # 3. GROQ LLM CALL
        context_str = "\n".join([f"- {d}" for d in relevant_docs])

        prompt = f"""
        Compare the CLAIM to the EVIDENCE.

        EVIDENCE:
        {context_str}

        CLAIM: 
        "{claim_text}"

        Rules:
        1. If evidence supports the claim, Verdict = "True"
        2. If evidence contradicts the claim, Verdict = "False"
        3. If evidence is unrelated, Verdict = "Unverifiable"

        Output JSON:
        {{
            "verdict": "True" | "False" | "Unverifiable",
            "reasoning": "Concise explanation"
        }}
        """

        raw_response = self.call_groq_llm(prompt)

        try:
            result = json.loads(raw_response)
            result["evidence"] = relevant_docs
            result["sources"] = list(set(evidence_sources))
            return result
        except:
            return {"verdict": "Error", "reasoning": "Parsing Error", "raw": raw_response}


checker = FactChecker()