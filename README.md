# KiraAIpet — AI Veterinary Triage for Greece

AI-powered veterinary triage assistant for dog and cat owners in Greece.
Built on Claude (Anthropic) + MSD Veterinary Manual citations.

## Benchmark

[![VetTriageBench-45](https://img.shields.io/badge/VetTriageBench--45-v1.0-blue)](https://github.com/chiinsurancebrokers/VetTriageBench-45)

KiraAIpet is evaluated against **VetTriageBench-45**, an open veterinary triage benchmark (45 vignettes, dogs + cats).

| Model | Accuracy (95% CI) | Unsafe undertriage |
|---|---|---|
| claude-sonnet-4-6 | 73.3% [59–84%] | ✅ 0% |
| gpt-4o | 80.0% [66–89%] | ⚠ 2.2% |

> **Key finding:** Claude Sonnet 4.6 achieved 0% unsafe undertriage — no EMERGENCY case was ever downgraded. GPT-4o missed one genuine emergency (feline urethral obstruction, PA014).

→ [Full results & methodology](https://github.com/chiinsurancebrokers/VetTriageBench-45)

## References

- Semigran et al. BMJ 2015;351:h3480
- Ruys et al. J Vet Emerg Crit Care 2012;22:303-312
- Groesser et al. J Vet Emerg Crit Care 2025. doi:10.1111/vec.70068
- Wong et al. Vet Record 2026;198(2):e46-e53
- MSD Veterinary Manual — merckvetmanual.com
