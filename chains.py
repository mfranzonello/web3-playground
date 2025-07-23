# chains.py

import yaml

def load_chains():
    with open("chains.yaml", "r") as f:
        return yaml.safe_load(f)

CHAINS = load_chains()

