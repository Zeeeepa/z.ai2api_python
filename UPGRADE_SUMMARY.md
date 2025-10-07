# GLM-4.6 + GLM-4.5V Upgrade Summary

## Changes Made

### 1. Script Updates (zai_cc.py)

**Model Configuration:**
```python
"models": [
    "GLM-4.6",        # Latest flagship model with 200K context
    "GLM-4.5",        # Previous flagship model
    "GLM-4.5-Air",    # Lightweight variant
    "GLM-4.5V"        # Vision/multimodal model
]
```

**Router Configuration:**
```python
"Router": {
    "default": "GLM,GLM-4.6",              # Use latest GLM-4.6 by default
    "background": "GLM,GLM-4.5-Air",       # Use Air for background tasks
    "think": "GLM,GLM-4.6",                # Use GLM-4.6 for reasoning
    "longContext": "GLM,GLM-4.6",          # GLM-4.6 has 200K context window
    "longContextThreshold": 100000,        # Increased from 60K to 100K
    "webSearch": "GLM,GLM-4.6",            # Use GLM-4.6 for search tasks
    "image": "GLM,GLM-4.5V"                # Use GLM-4.5V for vision tasks
}
```

### 2. Documentation Updates (ZAI_CC_README.md)

Added:
- Model comparison table
- Detailed usage guidelines for each model
- Vision task examples
- Performance benchmarks
- When to use which model guide

### 3. Key Improvements

**Performance:**
- 200K context window (66% increase)
- 30% more efficient token usage
- Outperforms Claude Sonnet 4 in coding benchmarks

**Features:**
- Dedicated vision model for image tasks
- Intelligent task-based routing
- Optimized for different use cases

**User Experience:**
- Automatic model selection
- No configuration needed
- Works out of the box

## Testing Results

✅ All models correctly configured
✅ Default routing to GLM-4.6
✅ Vision tasks route to GLM-4.5V
✅ Background tasks use GLM-4.5-Air
✅ Long context threshold properly set

## Usage

The script automatically handles everything. Just run:

```bash
python zai_cc.py
```

Claude Code will now:
- Use GLM-4.6 for general coding and reasoning
- Use GLM-4.5V for any image/vision tasks
- Use GLM-4.5-Air for background operations
- Support up to 200K tokens in context

## Model Selection Guide

**Use GLM-4.6 when:**
- Writing complex code
- Analyzing large codebases
- Advanced reasoning required
- Tool use and agentic workflows

**Use GLM-4.5V when:**
- Analyzing screenshots
- Understanding UI designs
- Converting images to code
- Visual debugging

**Use GLM-4.5-Air when:**
- Quick responses needed
- Simple code completion
- Background tasks
- Resource efficiency matters

## Benefits

1. **Better Performance**: 200K context, superior coding
2. **Vision Support**: Dedicated model for images
3. **Smart Routing**: Right model for each task
4. **Cost Effective**: Efficient token usage
5. **Future Proof**: Latest models supported

## Compatibility

- Works with Claude Code Router v1.0.47+
- Compatible with all existing configurations
- No breaking changes
- Drop-in upgrade

---

**Version:** 2.0
**Date:** 2025-10-07
**Status:** ✅ Tested and Ready
