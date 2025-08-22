import dataclasses
from typing import List, Dict, Optional

# --- The Agent Class ---
# This class represents the core logic of our Policy/Product Inquiry Agent.
# It uses a simplified Retrieval-Augmented Generation (RAG) pattern.
class PolicyInquiryAgent:
    def __init__(self):
        """Initializes the agent with an empty knowledge base."""
        self.knowledge_base: List[Dict[str, str]] = []

    def ingest_documents(self, documents: List[Dict[str, str]]) -> None:
        """
        Simulates the process of ingesting documents into a knowledge base.
        In a real-world system, this would involve creating vector embeddings
        and storing them in a vector database for efficient searching.
        """
        self.knowledge_base.extend(documents)
        print(f"Agent ingested {len(documents)} new documents.")

    def process_query(self, query: str) -> Dict:
        """
        Performs a simplified RAG process to answer a user query.

        1. Retrieval: Finds relevant documents from the knowledge base.
        2. Augmentation: Combines the user's query with the retrieved content.
        3. Generation: Uses the combined context to formulate a response.
        """
        print(f"\nProcessing user query: '{query}'")
        
        # --- 1. Simplified Retrieval ---
        # Instead of a complex vector search, we'll do a simple keyword match
        # to find documents that contain words from the user's query.
        keywords = query.lower().split()
        retrieved_documents = []
        for doc in self.knowledge_base:
            if any(keyword in doc['content'].lower() for keyword in keywords):
                retrieved_documents.append(doc)

        if not retrieved_documents:
            return {
                "response": "I'm sorry, I couldn't find any relevant information in my knowledge base.",
                "sources": []
            }

        # --- 2. Simplified Augmentation ---
        # We combine the user's query with the content of the retrieved documents.
        # This augmented prompt is what would be sent to a Large Language Model (LLM).
        context = "User query: " + query + "\n\nRelevant documents:\n"
        sources = []
        for doc in retrieved_documents:
            context += f"Source: {doc['source']}\nContent: {doc['content']}\n\n"
            sources.append(doc['source'])
        
        # --- 3. Simplified Generation ---
        # In a real system, a Large Language Model (LLM) would generate a
        # human-like response based on the `context` variable. Here, we'll
        # use a basic, rule-based approach to demonstrate the concept without
        # requiring an LLM API.
        
        response = ""
        # Check for keywords to formulate a basic, context-aware response.
        if "deductible" in query.lower() and "collision" in query.lower():
            response += "Based on the policy documents, collision deductibles are either $500 or $1,000, depending on the specific policy. "
        elif "comprehensive" in query.lower():
            response += "Comprehensive coverage protects against non-collision events like theft, fire, and weather damage. "
        elif "warranty" in query.lower():
            response += "The Model X has a 5-year, 60,000-mile limited warranty as specified in its product manual. "
        elif "assistance" in query.lower() and "roadside" in query.lower():
            response += "Roadside assistance is available with the auto policy, limited to 4 calls per year. "
        else:
            response = "I have located information related to your query. Please refer to the cited documents for details."

        return {
            "response": response.strip(),
            "sources": sources
        }
