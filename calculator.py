# calculator.py

def calculate_gas_fee(chain_info, complexity):
    base_fee = chain_info['gas_fee']
    if 'contract_multipliers' in chain_info:
        multiplier = chain_info['contract_multipliers'].get(complexity, 1)
    else:
        multiplier = 1
    scaled_fee = base_fee * multiplier
    
    return scaled_fee