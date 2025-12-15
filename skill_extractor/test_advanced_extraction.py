#!/usr/bin/env python3
"""
Test the advanced skills extractor vs the old one
"""

import json
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from nlp.skills_extractor_advanced import extract_skills_from_offers_advanced

# Load raw data
import csv
from pathlib import Path

data_path = Path(__file__).parent / 'data' / 'raw' / 'job_offers_raw.csv'

with open(data_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    offers = list(reader)

print(f"🔍 Testing Advanced Skills Extractor on {len(offers)} offers\n")

# Test on a few examples
test_indices = [3, 6, 10, 13, 14]  # Some IT jobs

for idx in test_indices[:3]:
    offer = offers[idx]
    print(f"\n{'='*80}")
    print(f"Job #{idx}: {offer['title']}")
    print(f"{'='*80}")
    print(f"Description preview: {offer['description'][:200]}...\n")
    
    # Extract with advanced method
    result = extract_skills_from_offers_advanced([offer])[0]
    
    print(f"✅ Skills Found ({result['num_skills']}):")
    print(f"   {result['skills']}\n")
    
    print("📊 By Category:")
    for category, skills in result['skills_categorized'].items():
        if skills:
            print(f"   {category}: {skills}")

print("\n" + "="*80)
print("Processing ALL offers with advanced extraction...")
print("="*80 + "\n")

# Process all offers
processed_offers = extract_skills_from_offers_advanced(offers)

# Save results
output_path = 'data/processed/job_offers_skills_advanced.json'
Path(output_path).parent.mkdir(parents=True, exist_ok=True)

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(processed_offers, f, indent=2, ensure_ascii=False)

print(f"✅ Saved to: {output_path}")

# Statistics
total_offers = len(processed_offers)
offers_with_skills = sum(1 for o in processed_offers if o.get('num_skills', 0) > 0)
avg_skills = sum(o.get('num_skills', 0) for o in processed_offers) / total_offers if total_offers > 0 else 0

print(f"\n📈 Statistics:")
print(f"   Total offers: {total_offers}")
print(f"   Offers with skills detected: {offers_with_skills}")
print(f"   Average skills per offer: {avg_skills:.1f}")

# Show top skills
from collections import Counter
all_skills = []
for offer in processed_offers:
    all_skills.extend(offer.get('skills', []))

top_skills = Counter(all_skills).most_common(20)
print(f"\n🏆 Top 20 Skills Found:")
for skill, count in top_skills:
    print(f"   {skill}: {count} offers")
