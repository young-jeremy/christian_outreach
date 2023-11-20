import re

def has_forbidden_content(content):
    # Tokenize the content into words (you might need to improve tokenization)
    words = nltk.word_tokenize(content.lower())

    # Check if any forbidden words or patterns are present
    for word in words:
        if word in forbidden_words:
            return True

    # You can also check for patterns using regular expressions
    # for pattern in forbidden_patterns:
    #     if re.search(pattern, content, re.IGNORECASE):
    #         return True

    return False
