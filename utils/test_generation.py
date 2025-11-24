from typing import List
from models.test_cases import TestCase
import spacy
from transformers import pipeline

# Load SpaCy English model
nlp = spacy.load("en_core_web_sm")  # Run: python -m spacy download en_core_web_sm if not already installed

# Load Hugging Face zero-shot classification pipeline
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Define feature synonym groups for keyword detection
KEYWORD_GROUPS = {
    "login": ["login", "sign in", "authenticate", "authentication"],
    "checkout": ["checkout", "payment", "purchase", "buy", "order completion"],
    "search": ["search", "find product", "lookup"],
    "registration": ["register", "sign up", "create account", "signup"],
}

# Define labels for zero-shot classification (customize as needed)
ZS_LABELS = list(KEYWORD_GROUPS.keys())

def keyword_present(text: str, keywords: List[str]) -> bool:
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)

def generate_keyword_based_test_cases(doc_text: str, html_text: str) -> List[TestCase]:
    test_cases = []
    id_counter = 1

    for feature, keywords in KEYWORD_GROUPS.items():
        if keyword_present(doc_text, keywords) or keyword_present(html_text, keywords):
            test_cases.append(TestCase(
                id=id_counter,
                title=f"Verify {feature} functionality",
                description=f"Test and validate the {feature} feature works correctly."
            ))
            id_counter += 1

    return test_cases

def generate_nlp_based_test_cases(text: str) -> List[TestCase]:
    doc = nlp(text)
    test_cases = []
    id_counter = 100  # Distinct range

    for ent in doc.ents:
        if ent.label_ in ["PRODUCT", "ORG", "EVENT"]:
            test_cases.append(TestCase(
                id=id_counter,
                title=f"Test {ent.text} functionality",
                description=f"Verify the {ent.text} performs as expected in the system."
            ))
            id_counter += 1

    return test_cases

def generate_transformer_based_test_cases(text: str) -> List[TestCase]:
    results = classifier(text, ZS_LABELS)
    test_cases = []
    id_counter = 200  # Distinct range

    for label, score in zip(results["labels"], results["scores"]):
        if score > 0.7:  # Threshold to filter confident predictions
            test_cases.append(TestCase(
                id=id_counter,
                title=f"Test {label} feature",
                description=f"Ensure the {label} functionality meets requirements with confidence {score:.2f}."
            ))
            id_counter += 1

    return test_cases

def generate_advanced_test_cases(doc_text: str, html_text: str) -> List[TestCase]:
    combined_text = doc_text + " " + html_text

    # Get test cases from all 3 methods
    keyword_cases = generate_keyword_based_test_cases(doc_text, html_text)
    nlp_cases = generate_nlp_based_test_cases(combined_text)
    transformer_cases = generate_transformer_based_test_cases(combined_text)

    # Combine and deduplicate by test case title
    combined = keyword_cases + nlp_cases + transformer_cases
    unique_cases = {}
    for test_case in combined:
        if test_case.title not in unique_cases:
            unique_cases[test_case.title] = test_case

    # Ensure there is at least one test case returned
    if not unique_cases:
        unique_cases["Default test case"] = TestCase(
            id=999,
            title="Default test case",
            description="No features identified; consider adding manual test cases."
        )

    return list(unique_cases.values())
