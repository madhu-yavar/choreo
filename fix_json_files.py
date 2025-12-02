import json

# Fix bias list
bias_data = [
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
  }
]

# Fix brand list
brand_data = [
  { "pattern": "competitorxyz", "type": "literal", "category": "COMPETITOR", "severity": 2 },
  { "pattern": "badbrand", "type": "literal", "category": "BRAND", "severity": 3 },
  { "pattern": "google", "type": "literal", "category": "COMPETITOR", "severity": 3 }
]

# Fix base list
base_data = [
  { "pattern": "fakecasino", "type": "literal", "category": "GAMBLING", "severity": 3 },
  { "pattern": "scamcoin",   "type": "literal", "category": "FINANCIAL", "severity": 4 },
  { "pattern": "extreme violence", "type": "literal", "category": "VIOLENCE", "severity": 5 },
  { "pattern": "\\bweapon(?:s)?\\b", "type": "regex", "category": "VIOLENCE", "severity": 4 },
  { "pattern": "ssn leak", "type": "literal", "category": "PRIVACY", "severity": 5 }
]

# Write files
with open('lists/banlist.bias.json', 'w') as f:
    json.dump(bias_data, f, indent=2)

with open('lists/banlist.brand.json', 'w') as f:
    json.dump(brand_data, f, indent=2)

with open('lists/banlist.base.json', 'w') as f:
    json.dump(base_data, f, indent=2)

print("JSON files fixed successfully!")