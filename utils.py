from typing import Optional, List

def parse_csv(s: Optional[str]) -> List[str]:
    if not s:
        return []
    return [p.strip() for p in s.split(",") if p.strip()]
