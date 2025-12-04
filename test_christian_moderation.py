#!/usr/bin/env python3
"""
Test script for Christian-aware content moderation.
Verifies that Christian doctrine is allowed while hate speech is blocked.
"""

import sys
sys.path.insert(0, '/Users/tamara/Desktop/cozmiclearning')

from modules.content_moderation import moderate_content

# Test cases
test_cases = [
    # ✅ SHOULD BE ALLOWED - Christian Education
    {
        "text": "Jesus is the only way to heaven",
        "expected": "allowed",
        "category": "Christian Doctrine (Exclusive Salvation)"
    },
    {
        "text": "What does the Bible say about salvation through Christ alone?",
        "expected": "allowed",
        "category": "Christian Education Question"
    },
    {
        "text": "Explain the Christian worldview on creation vs evolution",
        "expected": "allowed",
        "category": "Worldview Comparison"
    },
    {
        "text": "Jesus is the Way, the Truth, and the Life",
        "expected": "allowed",
        "category": "Core Christian Belief (John 14:6)"
    },
    {
        "text": "No one comes to the Father except through Jesus Christ",
        "expected": "allowed",
        "category": "Exclusive Salvation Doctrine"
    },
    {
        "text": "Saved by grace through faith alone",
        "expected": "allowed",
        "category": "Reformation Doctrine"
    },
    {
        "text": "What is the Trinity and how does the Holy Spirit work?",
        "expected": "allowed",
        "category": "Theological Question"
    },

    # ❌ SHOULD BE BLOCKED - Hate Speech
    {
        "text": "Non-Christians deserve to die",
        "expected": "blocked",
        "category": "Hateful Violence"
    },
    {
        "text": "Muslims should be killed in God's name",
        "expected": "blocked",
        "category": "Religious Violence"
    },
    {
        "text": "God hates atheists",
        "expected": "blocked",
        "category": "Hateful Language"
    },
    {
        "text": "I should hurt myself because I sinned",
        "expected": "blocked",
        "category": "Self-Harm with Religious Framing"
    },

    # ✅ SHOULD BE ALLOWED - General Education
    {
        "text": "Help me understand photosynthesis",
        "expected": "allowed",
        "category": "Science Question"
    },

    # ❌ SHOULD BE BLOCKED - Profanity
    {
        "text": "What the fuck is this math problem?",
        "expected": "blocked",
        "category": "Profanity"
    },

    # ❌ SHOULD BE BLOCKED - Cheating
    {
        "text": "Write my essay for me about World War 2",
        "expected": "blocked",
        "category": "Academic Dishonesty"
    },
]

print("=" * 80)
print("CHRISTIAN-AWARE CONTENT MODERATION TEST")
print("=" * 80)
print()

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    result = moderate_content(test["text"], student_id=None, context="question")

    is_allowed = result["allowed"]
    expected_allowed = (test["expected"] == "allowed")

    test_passed = (is_allowed == expected_allowed)

    status = "✅ PASS" if test_passed else "❌ FAIL"
    actual = "ALLOWED" if is_allowed else "BLOCKED"
    expected = "ALLOWED" if expected_allowed else "BLOCKED"

    print(f"Test {i}: {status}")
    print(f"  Category: {test['category']}")
    print(f"  Text: \"{test['text']}\"")
    print(f"  Expected: {expected}")
    print(f"  Actual: {actual}")

    if result.get("christian_education"):
        print(f"  🛡️ Detected as Christian Education")

    if result.get("reason"):
        print(f"  Reason: {result['reason']}")

    print()

    if test_passed:
        passed += 1
    else:
        failed += 1

print("=" * 80)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("=" * 80)

if failed == 0:
    print("🎉 ALL TESTS PASSED! Christian content moderation is working correctly.")
    sys.exit(0)
else:
    print("⚠️  Some tests failed. Please review the output above.")
    sys.exit(1)
