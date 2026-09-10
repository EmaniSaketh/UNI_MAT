import sys
import os
import pandas as pd
from sentence_transformers import SentenceTransformer, util

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from backend.adapters.alpha_adapter import process_alpha_data
from backend.adapters.beta_adapter import process_beta_data
from backend.core.nlp_cleaner import MaterialCleaner

class MaterialMatchingEngine:
    def __init__(self):
        print("📥 Loading embedding model (bge-small-en-v1.5)...")
        self.model = SentenceTransformer('BAAI/bge-small-en-v1.5')
        self.cleaner = MaterialCleaner()

    def find_matches(self, query_material, candidate_materials, top_k=3):
        """Finds the most similar materials using semantic embeddings and unit checks."""
        query_text = self.cleaner.clean_text(query_material.raw_data.description)
        
        # Prepare candidate texts
        candidate_texts = []
        for cand in candidate_materials:
            cand_text = self.cleaner.clean_text(cand.raw_data.description)
            candidate_texts.append(cand_text)

        # Encode query and candidates
        query_embedding = self.model.encode(query_text, convert_to_tensor=True)
        candidate_embeddings = self.model.encode(candidate_texts, convert_to_tensor=True)

        # Compute cosine similarities
        cos_scores = util.cos_sim(query_embedding, candidate_embeddings)[0]
        
        # Get top-k results
        top_results = torch.topk(cos_scores, k=min(top_k, len(candidate_materials)))
        
        matches = []
        for score, idx in zip(top_results.values, top_results.indices):
            idx = idx.item()
            cand = candidate_materials[idx]
            
            # Basic rule check for UOM compatibility
            uom_match = (self.cleaner.normalize_uom(query_material.raw_data.uom) == 
                         self.cleaner.normalize_uom(cand.raw_data.uom))
            
            final_confidence = float(score) * (1.0 if uom_match else 0.85)
            
            matches.append({
                "candidate_code": cand.source.original_material_code,
                "candidate_cpse": cand.source.cpse_id,
                "candidate_description": cand.raw_data.description,
                "semantic_score": round(float(score), 4),
                "uom_compatible": uom_match,
                "overall_confidence": round(final_confidence, 4)
            })
            
        return matches

if __name__ == "__main__":
    import torch
    
    engine = MaterialMatchingEngine()
    
    # Load data from Alpha and Beta
    alpha_recs = process_alpha_data("data/cpse_alpha.csv")
    beta_recs = process_beta_data("data/cpse_beta.csv")
    
    # Take the first item from Alpha as our query item
    query_item = alpha_recs[0]
    
    print(f"\n🔍 Query Material (Alpha): [{query_item.source.original_material_code}] {query_item.raw_data.description}")
    print("-" * 60)
    
    # Find matching items inside Beta dataset
    matches = engine.find_matches(query_item, beta_recs, top_k=3)
    
    for i, m in enumerate(matches, 1):
        print(f"{i}. CPSE: {m['candidate_cpse']} | Code: {m['candidate_code']}")
        print(f"   Desc: {m['candidate_description']}")
        print(f"   Confidence Score: {m['overall_confidence']} (Semantic: {m['semantic_score']})")
        print(f"   UOM Compatible: {m['uom_compatible']}\n")