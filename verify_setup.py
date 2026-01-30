import os
import sys

# Add current directory to path so we can import logic
sys.path.append(os.getcwd())

try:
    from logic import load_config, Randomizer, StoryLLM
    print("✅ Imports successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

config = load_config("config.yaml")
if config:
    print("✅ Config loaded")
    if "llm" in config:
        print(f"   Base URL: {config['llm'].get('base_url')}")
else:
    print("❌ Config loading failed")

elements = Randomizer.generate_random_elements()
print(f"✅ Randomizer test: {elements}")

print("✅ Setup verification complete. Ready to run Streamlit app.")
