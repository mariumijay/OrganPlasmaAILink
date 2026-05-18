import sys
from pathlib import Path
backend_path = Path("e:/opal projetx/opalai-simple (3)/opalai-simple/backend")
sys.path.append(str(backend_path))

print("Importing main...")
try:
    from main import app
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
