from magicai.rules_parser import parse_rules

rules = parse_rules()

print(f"Secciones: {len(rules)}")

print()

undying = rules["702.93"]

print(undying["title"])

print()

for rule in undying["rules"]:
    print(rule)