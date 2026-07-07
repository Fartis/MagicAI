KEYWORDS = {

    "flying",
    "trample",
    "deathtouch",
    "ward",
    "undying",
    "landfall",
    "hexproof",
    "flash",
    "lifelink",
    "vigilance",
    "reach",
    "menace",
    "haste",
    "first strike",
    "double strike"

}


def extract_keywords(question: str):

    q = question.lower()

    found = []

    for keyword in KEYWORDS:

        if keyword in q:
            found.append(keyword)

    return found