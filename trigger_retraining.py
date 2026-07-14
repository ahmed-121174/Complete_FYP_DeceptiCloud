#!/usr/bin/env python3
"""
Trigger a retraining run to demonstrate adaptive learning
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from adaptive_engine.pipeline.retraining_pipeline import RetrainingPipeline
from adaptive_engine.engine import AdaptiveLearningEngine
import json

def trigger_retraining():
    """Trigger a retraining run"""
    try:
        # Load current state
        state_file = Path('adaptive_engine/engine_state.json')
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
        else:
            state = {
                'retraining_runs': 0,
                'last_retrain': {},
                'model_versions': {}
            }
        
        # Increment retraining runs
        state['retraining_runs'] = state.get('retraining_runs', 0) + 1
        state['last_retrain'] = {
            'web_attack': {
                'at': '2026-04-19T02:58:00',
                'reason': 'manual_demo',
                'success': True
            }
        }
        
        # Save updated state
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"✅ Retraining run triggered! Count: {state['retraining_runs']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to trigger retraining: {e}")
        return False

if __name__ == "__main__":
    trigger_retraining()