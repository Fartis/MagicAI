import re


RULE_PATTERN = re.compile(r"\d+\.\d+[a-z]?")



def extract_rules(question: str):

    return RULE_PATTERN.findall(question)