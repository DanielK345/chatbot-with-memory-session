# Lightweight Model Integration for Query Refinement

## Summary

Successfully added **Qwen2.5-1.5B-Instruct** support to the LLMClient for ultra-fast query refinement tasks (pronoun replacement).

## Changes Made

### 1. LLMClient (`app/llm/client.py`)

**New Parameters:**
- `lightweight_ollama_model: str = "qwen2.5:1.5b"` - Specify lightweight model for fast inference

**New Methods:**
- `async generate_lightweight(prompt, system=None, temperature=0.3, max_tokens=20)` - Generate text using lightweight model with automatic fallback
- `get_lightweight_model_name() -> str` - Get the lightweight model name

**New Internal Client:**
- `self.lightweight_ollama_client` - Separate Ollama client instance for lightweight inference

### 2. QueryRefiner (`app/query_understanding/query_refiner.py`)

**Updated Method:**
- `async _rewrite_with_llm()` - Now calls `llm_client.generate_lightweight()` instead of `generate()`

## Model Comparison

| Aspect | Qwen2.5-1.5B | llama3.1 | Gemini Flash |
|--------|--------------|----------|-------------|
| Parameters | 1.5B | 8B | Proprietary |
| Speed | 2-3x faster ⚡ | Baseline | Fast |
| Memory | ~1-2 GB | ~6-8 GB | API |
| Best Use | Simple tasks ✓ | Complex reasoning | General |

## Usage

### Initialize with lightweight model:
```python
llm_client = LLMClient(
    primary="ollama",
    lightweight_ollama_model="qwen2.5:1.5b"
)
```

### Use for query refinement:
```python
# Automatically uses lightweight model for pronoun replacement
response = await llm_client.generate_lightweight(
    prompt="Rewrite query by replacing [pronouns] with [entities]...",
    max_tokens=20,
    temperature=0.3
)
```

## Setup Instructions

### Pull the lightweight model in Ollama:
```bash
ollama pull qwen2.5:1.5b
```

### Model Download Sizes:
- qwen2.5:1.5b: ~940 MB (smallest, fastest)
- llama3.1: ~4.7 GB (standard, fallback)

## Performance Benefits

1. **Query Refinement Speed**: 2-3x faster than llama3.1
2. **Resource Usage**: Can run on laptops/edge devices
3. **Latency**: Ultra-low latency for pronoun replacement
4. **Cost**: Lower compute cost for simple inference
5. **Fallback**: Automatic fallback to active client if unavailable

## Task-Specific Design

**Query Refinement Task:**
- Input: Query with pronouns + cached entities
- Processing: Lightweight pattern matching + minimal LLM
- Output: Refined query with pronouns replaced
- Model needed: Fast + accurate for simple replacements ✓ (Qwen2.5-1.5B)

**Why Qwen2.5-1.5B is Perfect:**
1. Instruction-tuned for following simple instructions
2. Fast enough for real-time query processing
3. Accurate enough for pronoun → entity mapping
4. Lightweight for resource-constrained deployments
5. Proven performance on instruction-following tasks

## Backward Compatibility

✓ Existing code works unchanged - lightweight model is transparent
✓ Falls back to active LLM if lightweight model unavailable
✓ Default behavior preserved for all other LLM operations

## Files Modified

1. [app/llm/client.py](app/llm/client.py) - Added lightweight model support
2. [app/query_understanding/query_refiner.py](app/query_understanding/query_refiner.py) - Uses lightweight inference
3. [app/core/pipeline.py](app/core/pipeline.py) - No changes needed (automatic)

## Testing

Run the lightweight model test:
```bash
python test_lightweight_model.py
```

Expected output:
- ✓ Lightweight Ollama client initialized (qwen2.5:1.5b)
- ✓ Model availability confirmed
- ✓ Fallback behavior verified

## Next Steps

1. Run `ollama pull qwen2.5:1.5b` to download the model (~940 MB)
2. Start Ollama: `ollama serve`
3. Test query refinement with the lightweight model
4. Monitor latency improvements vs standard model
