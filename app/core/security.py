import re

# Best-effort heuristic, not a bulletproof defense. See README "Known limitations":
# a determined attacker can phrase an injection attempt in ways this list won't
# catch. The primary defense is the hardened system prompt in app/services/llm/prompts.py;
# this is a second, cheap layer that catches the common/lazy attempts outright.
_SUSPICIOUS_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above) instructions",
    r"disregard (all |any )?(previous|prior|above) instructions",
    r"you are now (a|an|the)",
    r"new instructions\s*:",
    r"system prompt",
    r"reveal (your|the) (system )?prompt",
    r"forget (everything|all)( you (were|have been) told)? (above|before)",
    r"act as (an?|the) (ai|assistant|system|bot|model)",
    r"zignoruj (wszystkie |jakiekolwiek )?(poprzednie|powyższe) (instrukcje|polecenia)",
    r"pomiń (wszystkie |jakiekolwiek )?(poprzednie|powyższe) (instrukcje|polecenia)",
    r"jesteś teraz (asystentem|modelem|systemem)",
    r"nowe instrukcje\s*:",
    r"ujawnij (swoje|swój) (system prompt|instrukcje)",
    r"zapomnij (wszystko )?(powyżej|poprzednie)",
]

_COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in _SUSPICIOUS_PATTERNS]


def looks_like_prompt_injection(text: str) -> bool:
    return any(pattern.search(text) for pattern in _COMPILED_PATTERNS)
