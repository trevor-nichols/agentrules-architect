import os
import pytest


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_final_analysis_smoke():
    # Determine which provider is configured for 'final'
    from config.agents import MODEL_CONFIG
    model_cfg = MODEL_CONFIG.get("final")
    assert model_cfg is not None

    # Ensure the appropriate API key is present; skip if not configured
    provider = model_cfg.provider.value
    env_needed = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",  # google-genai
        "deepseek": "DEEPSEEK_API_KEY",
    }.get(provider)

    if env_needed and not os.getenv(env_needed):
        pytest.skip(f"Missing {env_needed} for live test of provider '{provider}'")

    # Run a minimal final analysis
    from core.analysis.final_analysis import FinalAnalysis

    fa = FinalAnalysis()
    result = await fa.run({"report": "Quick smoke input"}, project_structure=["."])

    # Provider responses vary, but should produce an analysis or a structured error
    assert isinstance(result, dict)
    assert "error" in result or "analysis" in result

