#!/usr/bin/env python3
"""
NLP Pipeline Runner - Complete text processing and skills extraction
Processes raw JSON job offers from scraping and outputs cleaned data with extracted skills.

Features:
- Loads raw JSON data from data/raw/
- Advanced text cleaning (HTML, URLs, special chars, normalization)
- Multi-strategy skills extraction (exact match, fuzzy match, regex patterns)
- Outputs to data/processed/ as JSON
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from nlp.text_cleaner import TextCleaner
from nlp.advanced_skills_extractor import SkillsExtractor
from nlp.nlp_pipeline import NLPPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nlp_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NLPRunner:
    """NLP pipeline runner for job offer processing"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent / 'data'
        self.raw_dir = self.data_dir / 'raw'
        self.processed_dir = self.data_dir / 'processed'
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.pipeline = NLPPipeline()
    
    def find_latest_raw_file(self) -> Path:
        """Find the most recent raw data file"""
        if not self.raw_dir.exists():
            raise FileNotFoundError(f"Raw data directory not found: {self.raw_dir}")
        
        json_files = list(self.raw_dir.glob('raw_offers_*.json'))
        if not json_files:
            raise FileNotFoundError(f"No raw JSON files found in {self.raw_dir}")
        
        latest = max(json_files, key=lambda p: p.stat().st_mtime)
        logger.info(f"📂 Found latest raw file: {latest.name}")
        return latest
    
    def run(self, input_file: Path = None) -> Dict:
        """Run complete NLP pipeline"""
        logger.info("\n" + "="*80)
        logger.info("🚀 STARTING NLP PIPELINE")
        logger.info("="*80)
        
        # Find input
        if input_file is None:
            input_file = self.find_latest_raw_file()
        else:
            input_file = Path(input_file)
        
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        logger.info(f"📥 Loading from: {input_file}")
        
        # Load
        with open(input_file, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        
        logger.info(f"✅ Loaded {len(jobs)} raw job offers\n")
        
        # Process
        logger.info(f"🔄 Processing with NLP Pipeline...")
        processed_jobs = self.pipeline.process_job_offers(jobs)
        
        # Statistics
        stats = self.pipeline.get_statistics(processed_jobs)
        
        # Save
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.processed_dir / f'processed_offers_{timestamp}.json'
        self.pipeline.save_processed_jobs(processed_jobs, str(output_file))
        
        # Display results
        logger.info("\n" + "="*80)
        logger.info("📊 NLP PROCESSING RESULTS")
        logger.info("="*80)
        logger.info(f"Total jobs processed: {stats['total_jobs']}")
        logger.info(f"Jobs with skills extracted: {stats['jobs_with_skills']}")
        logger.info(f"Coverage: {stats['coverage']}%")
        logger.info(f"Total unique skills found: {stats['total_unique_skills']}")
        logger.info(f"\n📍 Output saved to: {output_file}")
        
        logger.info("\n🏆 Top 20 Most Demanded Skills:")
        logger.info("-" * 80)
        for rank, (skill, count) in enumerate(stats['top_20_skills'], 1):
            pct = round((count / stats['total_jobs'] * 100), 1) if stats['total_jobs'] > 0 else 0
            bar_length = int(count / max([c for _, c in stats['top_20_skills']] + [1]) * 40)
            bar = "█" * bar_length
            logger.info(f"{rank:2d}. {skill:<35s} {count:3d} ({pct:5.1f}%) {bar}")
        
        logger.info("="*80)
        logger.info("✅ NLP PIPELINE COMPLETED SUCCESSFULLY\n")
        
        return {
            'input_file': str(input_file),
            'output_file': str(output_file),
            'stats': stats
        }


def main():
    """Main entry point"""
    try:
        runner = NLPRunner()
        result = runner.run()
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Input:  {result['input_file']}")
        print(f"Output: {result['output_file']}")
        print(f"Total jobs: {result['stats']['total_jobs']}")
        print(f"With skills: {result['stats']['jobs_with_skills']}")
        print(f"Coverage: {result['stats']['coverage']}%")
        print(f"Unique skills: {result['stats']['total_unique_skills']}")
        print("="*80)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        print(f"❌ Pipeline failed: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
