import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from websites.shared.site_factory import create_app

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_test_site.py '<json_config>'")
        sys.exit(1)
        
    config = json.loads(sys.argv[1])
    app = create_app(config)
    app.run(port=config['port'])
