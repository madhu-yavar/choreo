import json

# Enhanced bias patterns for more vigilant detection
bias_data = [
  # Gender bias
  {
    "pattern": "men are naturally better",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  {
    "pattern": "women are naturally better",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  {
    "pattern": "men are better than women",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  {
    "pattern": "women are better than men",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  {
    "pattern": "men are superior to women",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  {
    "pattern": "women are superior to men",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  {
    "pattern": "men are smarter than women",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  {
    "pattern": "women are smarter than men",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  
  # Racial bias
  {
    "pattern": "white people are better",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  {
    "pattern": "black people are better",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  {
    "pattern": "people of color are better",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  
  # Religious bias
  {
    "pattern": "christians are better",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  {
    "pattern": "muslims are better",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  {
    "pattern": "atheists are better",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  
  # Age bias
  {
    "pattern": "older people are better",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  {
    "pattern": "younger people are better",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  
  # Disability bias
  {
    "pattern": "disabled people are better",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  {
    "pattern": "able-bodied people are better",
    "type": "literal",
    "category": "BIAS",
    "severity": 4
  },
  
  # Regex patterns for more comprehensive detection
  {
    "pattern": "\\b(men|women)\\s+are\\s+(?:better|superior|smarter)\\s+than\\s+\\w+",
    "type": "regex",
    "category": "BIAS",
    "severity": 4
  },
  {
    "pattern": "\\b(white|black|brown)\\s+people\\s+are\\s+better\\s+than",
    "type": "regex",
    "category": "BIAS",
    "severity": 4
  },
  {
    "pattern": "\\b(christian|muslim|jewish|atheist)s?\\s+are\\s+better",
    "type": "regex",
    "category": "BIAS",
    "severity": 4
  }
]

# Write the enhanced bias patterns
with open('lists/banlist.bias.json', 'w') as f:
    json.dump(bias_data, f, indent=2)

print("Enhanced bias patterns updated successfully!")