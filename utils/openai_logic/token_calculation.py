# --- Pricing per 1M tokens (USD) ---
pricing = {
    "Batch": {
        "gpt-5": {"input": 0.625, "output": 5.00},
        "gpt-5-mini": {"input": 0.125, "output": 1.00},
        "gpt-5-nano": {"input": 0.025, "output": 0.20},
        "gpt-5-pro": {"input": 7.50, "output": 60.00},
        "gpt-4.1": {"input": 1.00, "output": 4.00},
        "gpt-4.1-mini": {"input": 0.20, "output": 0.80},
        "gpt-4.1-nano": {"input": 0.05, "output": 0.20},
        "gpt-4o": {"input": 1.25, "output": 5.00},
        "gpt-4o-mini": {"input": 0.075, "output": 0.30},
        "o3": {"input": 1.00, "output": 4.00},
        "o4-mini": {"input": 0.55, "output": 2.20},
    },
    "Flex": {
        "gpt-5": {"input": 0.625, "output": 5.00},
        "gpt-5-mini": {"input": 0.125, "output": 1.00},
        "gpt-5-nano": {"input": 0.025, "output": 0.20},
        "o3": {"input": 1.00, "output": 4.00},
        "o4-mini": {"input": 0.55, "output": 2.20},
    },
    "Standard": {
        "gpt-5": {"input": 1.25, "output": 10.00},
        "gpt-5-mini": {"input": 0.25, "output": 2.00},
        "gpt-5-nano": {"input": 0.05, "output": 0.40},
        "gpt-5-pro": {"input": 15.00, "output": 120.00},
        "gpt-4.1": {"input": 2.00, "output": 8.00},
        "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
        "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "o3": {"input": 2.00, "output": 8.00},
        "o4-mini": {"input": 1.10, "output": 4.40},
    },
    "Priority": {
        "gpt-5": {"input": 2.50, "output": 20.00},
        "gpt-5-mini": {"input": 0.45, "output": 3.60},
        "gpt-4.1": {"input": 3.50, "output": 14.00},
        "gpt-4.1-mini": {"input": 0.70, "output": 2.80},
        "gpt-4.1-nano": {"input": 0.20, "output": 0.80},
        "gpt-4o": {"input": 4.25, "output": 17.00},
        "gpt-4o-mini": {"input": 0.25, "output": 1.00},
        "o3": {"input": 3.50, "output": 14.00},
        "o4-mini": {"input": 2.00, "output": 8.00},
    },
}


def sum_input_output_token_cost(
    model, input_tokens, output_tokens, tier: str = "Standard"
):
    """
    Calculate the total USD cost for OpenAI API usage based on token counts and pricing tier.

    Parameters:
        model (str): Model name (e.g., 'gpt-4.1', 'gpt-4o', 'gpt-5-mini', etc.)
        input_tokens (int): Number of input tokens used (from API usage)
        output_tokens (int): Number of output tokens used (from API usage)
        tier (str): 'Batch', 'Flex', 'Standard', or 'Priority' (default: 'Standard')

    Returns:
        dict: Breakdown of input/output costs and total USD cost
    """

    tier = tier.capitalize()
    if tier not in pricing:
        raise ValueError(
            f"Invalid tier '{tier}'. Must be one of: Batch, Flex, Standard, Priority."
        )

    tier_pricing = pricing[tier]
    if model not in tier_pricing:
        raise ValueError(f"Pricing not found for model '{model}' in tier '{tier}'.")

    # --- Compute cost ---
    per_million = tier_pricing[model]
    input_cost = (input_tokens / 1_000_000) * per_million["input"]
    output_cost = (output_tokens / 1_000_000) * per_million["output"]
    total_cost = input_cost + output_cost

    return {
        "model": model,
        "tier": tier,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(total_cost, 6),
    }
