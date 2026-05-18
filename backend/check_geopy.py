import sys
try:
    import geopy
    print(f"geopy installed: {geopy.__version__}")
except ImportError:
    print("geopy NOT installed")
