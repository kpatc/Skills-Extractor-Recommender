#!/usr/bin/env python3
"""
Compare old vs new skills extraction
"""

import json
import csv
from pathlib import Path
from collections import Counter

# Load raw data
data_path = Path(__file__).parent / 'data' / 'raw' / 'job_offers_raw.csv'
with open(data_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    offers = list(reader)

# Test with old extractor (if available)
try:
    from nlp.skills_extractor_v2 import extract_skills_from_jobs
    offers_old = [dict(o) for o in offers]
    results_old = extract_skills_from_jobs(offers_old)
    has_old = True
except:
    has_old = False
    print("⚠️  Old extractor not available for comparison\n")

# Test with new extractor
from nlp.skills_extractor_advanced import extract_skills_from_offers_advanced
offers_new = [dict(o) for o in offers]
results_new = extract_skills_from_offers_advanced(offers_new)

print("="*80)
print("SKILLS EXTRACTION COMPARISON: OLD vs NEW")
print("="*80 + "\n")

if has_old:
    # Count offers with skills
    offers_with_old = sum(1 for o in results_old if o.get('num_skills', 0) > 0)
    offers_with_new = sum(1 for o in results_new if o.get('num_skills', 0) > 0)
    
    # Average skills
    avg_old = sum(o.get('num_skills', 0) for o in results_old) / len(results_old)
    avg_new = sum(o.get('num_skills', 0) for o in results_new) / len(results_new)
    
    print("📊 STATISTICS:")
    print(f"   Total offers: {len(offers)}\n")
    print(f"   Old Extractor:")
    print(f"     - Offers with skills: {offers_with_old}/{len(offers)} ({100*offers_with_old/len(offers):.0f}%)")
    print(f"     - Average skills/offer: {avg_old:.1f}\n")
    print(f"   New Extractor:")
    print(f"     - Offers with skills: {offers_with_new}/{len(offers)} ({100*offers_with_new/len(offers):.0f}%)")
    print(f"     - Average skills/offer: {avg_new:.1f}")
    print(f"     - IMPROVEMENT: +{offers_with_new-offers_with_old} offers, +{avg_new-avg_old:.1f} avg skills\n")

# Show top skills with new extractor
all_skills = []
for offer in results_new:
    all_skills.extend(offer.get('skills', []))

top_skills = Counter(all_skills).most_common(15)
print("🏆 Top Skills Found (New Extractor):")
for skill, count in top_skills:
    print(f"   {skill}: {count} offers")

print("\n" + "="*80)
print("DETAILED COMPARISON ON SAMPLE JOBS")
print("="*80 + "\n")

# Compare on a few jobs
test_jobs = [13, 23, 24, 25, 27]  # Python, Senior Dev, Fullstack, DevOps

for idx in test_jobs:
    if idx >= len(offers):
        continue
    
    job = offers[idx]
    new_skills = results_new[idx]['skills']
    
    print(f"\n📌 Job #{idx}: {job['title'][:60]}")
    print(f"   New Skills: {new_skills}")
    
    if has_old:
        old_skills = results_old[idx].get('skills', [])
        print(f"   Old Skills: {old_skills}")
        
        # Show what's new
        new_found = set(new_skills) - set(old_skills)
        if new_found:
            print(f"   ✅ NEWLY FOUND: {sorted(new_found)}")

print("\n" + "="*80)
