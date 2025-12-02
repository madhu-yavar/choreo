# Enhanced Ban Service Implementation Plan

## Phase 1: Basic NER Integration

### Dependencies to Add
```bash
pip install spacy
python -m spacy download en_core_web_sm
```

### Core Logic
1. Extract organization names using spaCy NER
2. Check extracted names against competitor database
3. Consider context keywords for competition detection

### Example Code Structure
```python
import spacy
from typing import List, Dict

class EnhancedBanMatcher:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.competitors = self.load_competitors()
        self.competition_contexts = [
            "better than", "worse than", "compared to", "vs", "versus",
            "competitor", "alternative to", "beats", "loses to"
        ]
    
    def load_competitors(self) -> List[str]:
        # Load from database/JSON file
        return ["Microsoft", "Apple", "Google", "Amazon", "competitorxyz"]
    
    def extract_organizations(self, text: str) -> List[str]:
        doc = self.nlp(text)
        organizations = []
        for ent in doc.ents:
            if ent.label_ == "ORG":
                organizations.append(ent.text)
        return organizations
    
    def detect_competition_context(self, text: str) -> bool:
        text_lower = text.lower()
        return any(context in text_lower for context in self.competition_contexts)
    
    def check_competitor_mentions(self, text: str) -> List[Dict]:
        organizations = self.extract_organizations(text)
        competition_context = self.detect_competition_context(text)
        
        violations = []
        for org in organizations:
            if org in self.competitors and competition_context:
                violations.append({
                    "type": "competitor",
                    "value": org,
                    "context": "competition_mention"
                })
        return violations
```

## Phase 2: Context-Aware Detection

### Enhanced Logic
1. Use sentence-level analysis
2. Identify comparative statements
3. Detect sentiment toward mentioned companies

### Example Enhancement
```python
def analyze_competitor_context(self, text: str, organization: str) -> Dict:
    doc = self.nlp(text)
    for sent in doc.sents:
        if organization in sent.text:
            # Check for comparative language
            if any(comp in sent.text.lower() for comp in ["better", "worse", "than", "compared"]):
                return {"context": "comparison", "confidence": 0.8}
            # Check for negative sentiment
            elif self.detect_negative_sentiment(sent.text):
                return {"context": "negative_mention", "confidence": 0.6}
    return {"context": "neutral", "confidence": 0.3}
```

## Phase 3: Dynamic Competitor Management

### Features
1. API endpoints to add/remove competitors
2. Industry categorization
3. Confidence scoring
4. False positive reduction

### Admin API Example
```python
@app.post("/admin/competitors")
def add_competitor(req: CompetitorRequest, x_api_key: str = Header(None)):
    # Add competitor to database
    # Update matcher cache
    return {"status": "success", "message": f"Added {req.name}"}
```

## Benefits of This Approach

1. **Intelligent Detection**: Finds competitors even if not in original list
2. **Context Awareness**: Understands when companies are mentioned as competitors
3. **Scalable**: Easy to add new competitors and industries
4. **Configurable**: Adjustable confidence thresholds
5. **Maintainable**: Modular design that integrates with existing system