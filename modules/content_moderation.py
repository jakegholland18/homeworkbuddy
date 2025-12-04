# modules/content_moderation.py
"""
Content Moderation System for CozmicLearning

Multi-layered safety system to protect students and platform integrity:
1. OpenAI Moderation API - Flag harmful content
2. Christian education allowlist - Preserve faith-based learning
3. Keyword filtering - Block inappropriate words/phrases
4. Input validation - Sanitize and limit input
5. Rate limiting - Prevent spam/abuse
6. Activity logging - Track all interactions for review

FAITH-AWARE: This system allows Christian education content including
core doctrines like salvation through Christ alone, while blocking
hate speech and abuse of religious content.
"""

import os
import re
from datetime import datetime, timedelta
from openai import OpenAI


# -------------------------------------------------------
# CHRISTIAN EDUCATION ALLOWLIST
# -------------------------------------------------------
CHRISTIAN_EDUCATION_KEYWORDS = [
    # Bible study
    "bible", "scripture", "verse", "testament", "psalm", "proverb",
    "gospel", "biblical", "bible study", "what does the bible say",
    "scripture says", "god's word",

    # Christian worldview & doctrine
    "christian worldview", "faith perspective", "god's design",
    "christian view", "how does god", "what does god",
    "jesus is the way", "jesus is the only way", "salvation through christ",
    "born again", "saved by grace", "faith alone",

    # Core Christian beliefs (salvation, trinity, etc.)
    "jesus", "christ", "holy spirit", "trinity", "salvation",
    "grace", "faith", "prayer", "worship", "creation",
    "sin", "redemption", "forgiveness", "heaven", "eternal life",
    "resurrection", "crucifixion", "atonement", "justification",

    # Biblical characters & books
    "moses", "david", "abraham", "paul", "peter", "mary", "noah",
    "genesis", "exodus", "matthew", "john", "romans", "revelation",

    # Christian subjects
    "theology", "doctrine", "church history", "apologetics",
    "christian ethics", "biblical worldview", "intelligent design"
]

CHRISTIAN_DOCTRINE_PATTERNS = [
    # Salvation doctrine (allow exclusive claims about Christ)
    r'jesus is the (only )?way',
    r'salvation (through|in|by) (jesus|christ) (alone)?',
    r'no one comes to (the father|heaven) (except|but) (through|by) (jesus|christ)',
    r'jesus (is )?the way,? the truth,? and the life',
    r'saved by grace (through faith)?',
    r'born again',

    # Trinity & deity of Christ
    r'jesus is god',
    r'trinity',
    r'father,? son,? and holy spirit',

    # Creation & worldview
    r'god created',
    r'intelligent design',
    r'christian (worldview|perspective) (on|of)',

    # Comparative worldview (educational)
    r'christian (and|vs|versus|compared to) (secular|atheist|humanist|scientific)',
    r'biblical (vs|versus|compared to) (secular|scientific)',
    r'how (is|does).*different.*from.*(secular|atheist)',
]

def is_christian_education_content(text: str) -> bool:
    """
    Detect if question is legitimate Christian education.
    Allows core Christian doctrine including exclusive salvation claims.

    Returns True if content is Christian educational, False otherwise.
    """
    text_lower = text.lower()

    # Check for Christian education keywords
    for keyword in CHRISTIAN_EDUCATION_KEYWORDS:
        if keyword in text_lower:
            return True

    # Check for Christian doctrine patterns
    for pattern in CHRISTIAN_DOCTRINE_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True

    return False


def is_respectful_christian_inquiry(text: str) -> bool:
    """
    Distinguish between educational Christian questions and hate speech.

    Allows: "Jesus is the only way to heaven" (doctrine)
    Blocks: "Non-Christians deserve to die" (hate speech)

    Returns True if respectful, False if hateful.
    """
    text_lower = text.lower()

    # RED FLAGS: Religious content used for hate/violence
    hate_patterns = [
        # Violence/harm against people
        r'(kill|hurt|attack|murder|harm).*\b(muslims?|jews?|hindus?|atheists?|non-believers?)',
        r'\b(muslims?|jews?|hindus?|atheists?|non-believers?).*\b(should|deserve|must|need to)\s+(die|be killed|suffer|burn)',

        # Hateful/dehumanizing language
        r'\b(muslims?|jews?|hindus?|atheists?).*\b(are|is)\s+(evil|demons?|satanic|wicked)',
        r'(god|jesus|bible)\s+(hates|curses|condemns)\s+\b(muslims?|jews?|hindus?|atheists?|gays?|lgbt)',

        # Promoting violence in God's name
        r'(kill|attack|hurt).*in.*(god\'?s?|jesus|christ\'?s?).*name',
        r'god (wants|commands|tells) (us|you|me) to (kill|hurt|attack)',

        # Self-harm with religious framing
        r'(god wants|jesus wants|i should|i need to).*\b(kill|hurt|harm|cut) (myself|me)',
        r'(sinned|sin) so (i should|i must|i deserve to) (die|hurt myself)',
    ]

    for pattern in hate_patterns:
        if re.search(pattern, text_lower):
            return False  # Block hate speech/violence

    # GREEN FLAGS: Educational, theological inquiry (always allow)
    educational_patterns = [
        r'what does (the )?bible say',
        r'christian (worldview|perspective|view|doctrine|belief) (on|about|of)',
        r'(how|why) (do |does )(christians?|jesus|god|the bible)',
        r'explain.*christian',
        r'bible (verse|study|lesson|passage)',
        r'scripture (about|on|says)',
        r'jesus (is|taught|said)',
        r'salvation (through|in|by)',
        r'(is|are) there.*other ways? to',  # "Are there other ways to heaven?" - allow theological inquiry
    ]

    for pattern in educational_patterns:
        if re.search(pattern, text_lower):
            return True  # Allow educational questions

    # Default: Allow unless hate detected above
    return True


# -------------------------------------------------------
# OpenAI Moderation API
# -------------------------------------------------------
def check_openai_moderation(text: str) -> dict:
    """
    Use OpenAI's Moderation API to check for policy violations.
    
    Returns dict:
    {
        "flagged": bool,
        "categories": dict of categories that were flagged,
        "category_scores": dict of confidence scores,
        "reason": str description of why it was flagged
    }
    """
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.moderations.create(input=text)
        
        result = response.results[0]
        
        flagged_categories = []
        if result.flagged:
            # Collect which categories were flagged
            for category, is_flagged in result.categories.model_dump().items():
                if is_flagged:
                    flagged_categories.append(category.replace('_', ' ').replace('/', ' or '))
        
        return {
            "flagged": result.flagged,
            "categories": result.categories.model_dump(),
            "category_scores": result.category_scores.model_dump(),
            "reason": ", ".join(flagged_categories) if flagged_categories else None
        }
    
    except Exception as e:
        # SECURITY FIX: Fail closed - block content when API is down
        # This prevents bypassing safety checks during outages
        print(f"🚨 Moderation API error: {e}")
        return {
            "flagged": True,  # ⚠️ Changed to True (fail closed)
            "categories": {},
            "category_scores": {},
            "reason": "Content moderation system temporarily unavailable",
            "error": str(e),
            "fail_closed": True  # Flag to indicate this was a safety failure
        }


# -------------------------------------------------------
# Keyword Filtering
# -------------------------------------------------------
BLOCKED_KEYWORDS = [
    # Profanity (expanded with variations)
    r'\bf+u+c+k+',
    r'\bs+h+i+t+',
    r'\bb+i+t+c+h+',
    r'\ba+s+s+h+o+l+e+',
    r'\bd+a+m+n+(?!ation)',  # Allow "damnation" in Christian context
    r'\bc+r+a+p+',
    r'\bp+i+s+s+',
    r'\bc+o+c+k+',
    r'\bp+u+s+s+y+',
    r'\bc+u+n+t+',
    r'\bm+o+t+h+e+r+f+',
    r'\bb+a+s+t+a+r+d+',

    # Sexual content (explicit)
    r'\bsex+y+',
    r'\bp+o+r+n+',
    r'\bn+u+d+e+',
    r'\bn+a+k+e+d+',
    r'\bm+a+s+t+u+r+b+',
    r'\bo+r+g+a+s+m+',
    r'\be+r+o+t+i+c+',

    # Violence & weapons (unless historical/educational)
    r'\b(how to |make a )bomb',
    r'\b(build|create|make).*(gun|weapon|explosive)',
    r'(kill|murder|hurt).*(people|someone|yourself)',

    # Drugs & alcohol (non-educational)
    r'\bget+ing?\s+high',
    r'\bsmoke\s+(weed|pot|marijuana)',
    r'\bdo+ing?\s+drugs',
    r'(buy|sell|get).*(cocaine|heroin|meth|lsd)',

    # Cheating/academic dishonesty
    r'write.{0,20}essay.{0,20}for.{0,20}me',
    r'do.{0,20}homework.{0,20}for.{0,20}me',
    r'complete.{0,20}assignment.{0,20}for',
    r'give.{0,20}me.{0,20}(the\s+)?answers?',
    r'test.{0,20}answers?',
    r'\bcheat(?!ah)',  # Allow "cheetah"
    r'solve.{0,20}(this|these|my).{0,20}problems?.{0,20}for.{0,20}me',

    # Prompt injection / jailbreak attempts
    r'\bhack',
    r'\bexploit',
    r'\bjailbreak',
    r'ignore.{0,20}(previous|above|prior|system|all).{0,20}(instructions|prompts?|rules|commands?)',
    r'pretend.{0,20}(you.{0,20})?are.{0,20}(not\s+)?a',
    r'act.{0,20}as.{0,20}(if|though)',
    r'disregard.{0,20}(previous|system|safety)',
    r'forget.{0,20}(your|the).{0,20}(rules|instructions|guidelines)',
    r'you.{0,20}are.{0,20}now.{0,20}(a|in)',

    # Personal information requests (phishing)
    r'(give|tell).{0,20}me.{0,20}your.{0,20}(password|email|phone)',
    r'what.{0,20}is.{0,20}your.{0,20}(real\s+)?name',
]

def check_keyword_filter(text: str) -> dict:
    """
    Check text against blocked keyword patterns.
    
    Returns dict:
    {
        "flagged": bool,
        "matched_pattern": str or None,
        "reason": str description
    }
    """
    text_lower = text.lower()
    
    for pattern in BLOCKED_KEYWORDS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return {
                "flagged": True,
                "matched_pattern": pattern,
                "reason": "Contains inappropriate or blocked content"
            }
    
    return {
        "flagged": False,
        "matched_pattern": None,
        "reason": None
    }


# -------------------------------------------------------
# Input Validation
# -------------------------------------------------------
def validate_input(text: str, max_length: int = 1000) -> dict:
    """
    Validate and sanitize user input.
    
    Returns dict:
    {
        "valid": bool,
        "sanitized_text": str,
        "reason": str if invalid
    }
    """
    if not text or not isinstance(text, str):
        return {
            "valid": False,
            "sanitized_text": "",
            "reason": "Question cannot be empty"
        }
    
    # Remove excessive whitespace
    sanitized = " ".join(text.split())
    
    # Check length
    if len(sanitized) < 3:
        return {
            "valid": False,
            "sanitized_text": sanitized,
            "reason": "Question is too short (minimum 3 characters)"
        }
    
    if len(sanitized) > max_length:
        return {
            "valid": False,
            "sanitized_text": sanitized[:max_length],
            "reason": f"Question is too long (maximum {max_length} characters)"
        }
    
    # Check for spam patterns (repeated characters)
    if re.search(r'(.)\1{20,}', sanitized):
        return {
            "valid": False,
            "sanitized_text": sanitized,
            "reason": "Question contains spam or invalid patterns"
        }
    
    # Check for URL/link spam (basic check)
    if re.search(r'(https?://|www\.)\S+', sanitized, re.IGNORECASE):
        # Allow educational links but flag for review
        pass
    
    return {
        "valid": True,
        "sanitized_text": sanitized,
        "reason": None
    }


# -------------------------------------------------------
# Rate Limiting (Per-Student)
# -------------------------------------------------------
# In-memory storage for rate limiting (production should use Redis/database)
_rate_limit_tracker = {}

def check_rate_limit(student_id: int, max_requests: int = 20, window_minutes: int = 60) -> dict:
    """
    Check if student has exceeded rate limit.
    
    Returns dict:
    {
        "allowed": bool,
        "remaining": int,
        "reset_time": datetime or None
    }
    """
    now = datetime.utcnow()
    window_start = now - timedelta(minutes=window_minutes)
    
    # Initialize or clean old requests
    if student_id not in _rate_limit_tracker:
        _rate_limit_tracker[student_id] = []
    
    # Remove requests outside current window
    _rate_limit_tracker[student_id] = [
        timestamp for timestamp in _rate_limit_tracker[student_id]
        if timestamp > window_start
    ]
    
    current_count = len(_rate_limit_tracker[student_id])
    
    if current_count >= max_requests:
        # Find oldest request to determine reset time
        oldest = min(_rate_limit_tracker[student_id])
        reset_time = oldest + timedelta(minutes=window_minutes)
        
        return {
            "allowed": False,
            "remaining": 0,
            "reset_time": reset_time,
            "reason": f"Rate limit exceeded. Maximum {max_requests} questions per {window_minutes} minutes."
        }
    
    # Add current request
    _rate_limit_tracker[student_id].append(now)
    
    return {
        "allowed": True,
        "remaining": max_requests - current_count - 1,
        "reset_time": None,
        "reason": None
    }


# -------------------------------------------------------
# Severity Assessment
# -------------------------------------------------------
def assess_severity(moderation_data: dict) -> str:
    """
    Determine severity level based on moderation results.
    
    Returns: "low", "medium", or "high"
    """
    openai_check = moderation_data.get("openai_moderation", {})
    keyword_check = moderation_data.get("keyword_filter", {})
    
    if not openai_check.get("flagged") and not keyword_check.get("flagged"):
        return "low"
    
    # High severity categories
    high_severity_categories = [
        "sexual/minors", "violence/graphic", "self-harm/intent", 
        "self-harm/instructions", "hate/threatening"
    ]
    
    if openai_check.get("flagged"):
        categories = openai_check.get("categories", {})
        for category in high_severity_categories:
            if categories.get(category.replace("/", "_"), False):
                return "high"
        
        # Check confidence scores
        scores = openai_check.get("category_scores", {})
        max_score = max(scores.values()) if scores else 0
        if max_score > 0.8:
            return "high"
        elif max_score > 0.5:
            return "medium"
    
    # Keyword-based severity
    if keyword_check.get("flagged"):
        pattern = keyword_check.get("matched_pattern", "")
        # Profanity is medium, cheating/jailbreak is low
        if any(p in pattern for p in ["f+u+c+k+", "b+i+t+c+h+", "a+s+s+h+o+l+e+"]):
            return "medium"
        return "low"
    
    return "low"


# -------------------------------------------------------
# Master Moderation Function
# -------------------------------------------------------
def moderate_content(text: str, student_id: int = None, context: str = "question") -> dict:
    """
    Run all moderation checks on user input.
    
    Args:
        text: The user's question/message
        student_id: Student ID for rate limiting (optional)
        context: Type of interaction ("question", "chat", "practice")
    
    Returns dict:
    {
        "allowed": bool - Whether content should be processed,
        "flagged": bool - Whether content was flagged (for logging),
        "sanitized_text": str - Cleaned input text,
        "reason": str - Why content was blocked/flagged,
        "severity": str - Severity level ("low", "medium", "high"),
        "warning": str - Warning message for student (if applicable),
        "moderation_data": dict - Full details for logging
    }
    """
    result = {
        "allowed": True,
        "flagged": False,
        "sanitized_text": text,
        "reason": None,
        "severity": "low",
        "warning": None,
        "moderation_data": {},
        "christian_education": False
    }

    # Step 1: Input validation
    validation = validate_input(text)
    result["moderation_data"]["validation"] = validation

    if not validation["valid"]:
        result["allowed"] = False
        result["flagged"] = True
        result["reason"] = validation["reason"]
        return result

    result["sanitized_text"] = validation["sanitized_text"]

    # Step 2: CHRISTIAN EDUCATION DETECTION (NEW!)
    # Check if this is legitimate Christian educational content
    is_christian_ed = is_christian_education_content(validation["sanitized_text"])
    result["christian_education"] = is_christian_ed
    result["moderation_data"]["christian_education"] = is_christian_ed

    if is_christian_ed:
        # Verify it's respectful (not hate speech disguised as religion)
        if not is_respectful_christian_inquiry(validation["sanitized_text"]):
            result["allowed"] = False
            result["flagged"] = True
            result["reason"] = "Religious content must be respectful and educational."
            result["severity"] = "high"
            return result

        # Christian education content: Skip religious content flags from OpenAI
        # but still check critical safety categories
        openai_check = check_openai_moderation(validation["sanitized_text"])
        result["moderation_data"]["openai_moderation"] = openai_check

        # For Christian content, only block if CRITICAL safety issues
        if openai_check.get("flagged"):
            # Check if it was flagged due to OpenAI API failure
            if openai_check.get("fail_closed"):
                # API is down - use enhanced keyword filter as fallback
                keyword_check = check_keyword_filter(validation["sanitized_text"])
                if keyword_check["flagged"]:
                    result["allowed"] = False
                    result["flagged"] = True
                    result["reason"] = "Content blocked by safety filter"
                    return result
                # Keyword filter passed - allow Christian content
                result["allowed"] = True
                result["flagged"] = False
                result["warning"] = "✝️ Christian educational content approved"
                return result

            # Check only critical safety categories
            categories = openai_check.get("categories", {})
            critical_flags = [
                categories.get("violence", False),
                categories.get("violence_graphic", False),
                categories.get("self-harm", False),
                categories.get("self-harm_intent", False),
                categories.get("self-harm_instructions", False),
                categories.get("sexual", False),
                categories.get("sexual_minors", False),
            ]

            if any(critical_flags):
                result["allowed"] = False
                result["flagged"] = True
                result["reason"] = "Content contains inappropriate material"
                result["severity"] = "high"
                return result

        # Christian education content approved!
        result["allowed"] = True
        result["flagged"] = False
        result["warning"] = "✝️ Christian educational content approved"
        return result

    # Step 3: Rate limiting (if student_id provided)
    # NOTE: Rate limiting disabled per user request - will be plan-based
    # if student_id is not None:
    #     rate_check = check_rate_limit(student_id)
    #     result["moderation_data"]["rate_limit"] = rate_check
    #
    #     if not rate_check["allowed"]:
    #         result["allowed"] = False
    #         result["flagged"] = True
    #         result["reason"] = rate_check["reason"]
    #         return result

    # Step 4: Keyword filtering
    keyword_check = check_keyword_filter(validation["sanitized_text"])
    result["moderation_data"]["keyword_filter"] = keyword_check

    if keyword_check["flagged"]:
        result["allowed"] = False
        result["flagged"] = True
        result["reason"] = "Your question contains inappropriate content. Please ask educational questions only."
        return result

    # Step 5: OpenAI Moderation API
    openai_check = check_openai_moderation(validation["sanitized_text"])
    result["moderation_data"]["openai_moderation"] = openai_check

    if openai_check["flagged"]:
        # Check if API failed (fail-closed mode)
        if openai_check.get("fail_closed"):
            result["allowed"] = False
            result["flagged"] = True
            result["reason"] = "Our safety system is temporarily unavailable. Please try again in a few minutes."
            result["severity"] = "medium"
            return result

        result["allowed"] = False
        result["flagged"] = True
        categories = openai_check["reason"] or "policy violations"
        result["reason"] = f"Your question was flagged for: {categories}. Please ask appropriate educational questions."
        result["warning"] = "⚠️ This type of content violates our community guidelines. Please keep questions educational and respectful."

    # Assess severity level
    result["severity"] = assess_severity(result["moderation_data"])

    # All checks passed
    return result


# -------------------------------------------------------
# Helper: Get flagged reason summary
# -------------------------------------------------------
def get_moderation_summary(moderation_result: dict) -> str:
    """
    Create human-readable summary of moderation result for logging.
    """
    if not moderation_result.get("flagged"):
        return "Passed all checks"
    
    parts = []
    data = moderation_result.get("moderation_data", {})
    
    if data.get("validation", {}).get("valid") is False:
        parts.append(f"Validation: {data['validation'].get('reason')}")
    
    if data.get("rate_limit", {}).get("allowed") is False:
        parts.append("Rate limit exceeded")
    
    if data.get("keyword_filter", {}).get("flagged"):
        parts.append(f"Keyword filter: {data['keyword_filter'].get('matched_pattern')}")
    
    if data.get("openai_moderation", {}).get("flagged"):
        parts.append(f"OpenAI: {data['openai_moderation'].get('reason')}")
    
    return " | ".join(parts) if parts else "Unknown reason"


# -------------------------------------------------------
# AI Response Filtering (Output Moderation)
# -------------------------------------------------------
def moderate_ai_response(response_text: str, original_question: str = "", student_id: int = None) -> dict:
    """
    Moderate AI-generated responses before showing to students.

    This ensures the AI didn't:
    - Generate inappropriate content
    - Leak personal information
    - Ignore safety guidelines
    - Provide harmful instructions

    Args:
        response_text: The AI's generated response
        original_question: The student's original question (for context)
        student_id: Student ID for logging

    Returns dict:
    {
        "allowed": bool - Whether to show response to student,
        "flagged": bool - Whether response was flagged,
        "sanitized_text": str - Cleaned response (PII redacted),
        "reason": str - Why response was blocked,
        "requires_regeneration": bool - If True, should retry with stricter prompt
    }
    """
    result = {
        "allowed": True,
        "flagged": False,
        "sanitized_text": response_text,
        "reason": None,
        "requires_regeneration": False
    }

    # Step 1: Check for PII leakage (emails, phones, addresses)
    pii_patterns = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL REDACTED]'),  # Email
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE REDACTED]'),  # Phone number
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN REDACTED]'),  # SSN
        (r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[CARD REDACTED]'),  # Credit card
    ]

    sanitized = response_text
    for pattern, replacement in pii_patterns:
        if re.search(pattern, sanitized):
            result["flagged"] = True
            result["reason"] = "Response contained personal information (redacted)"
            sanitized = re.sub(pattern, replacement, sanitized)

    result["sanitized_text"] = sanitized

    # Step 2: Run through OpenAI moderation
    mod_check = check_openai_moderation(sanitized)

    if mod_check.get("flagged") and not mod_check.get("fail_closed"):
        # AI generated inappropriate content!
        categories = mod_check.get("categories", {})

        # Critical safety violations - block completely
        critical = ["violence/graphic", "sexual", "sexual/minors", "self-harm/instructions"]
        if any(categories.get(cat.replace("/", "_"), False) for cat in critical):
            result["allowed"] = False
            result["flagged"] = True
            result["requires_regeneration"] = True
            result["reason"] = "AI generated unsafe content - regenerating with stricter guidelines"
            return result

    # Step 3: Check for homework completion (AI shouldn't complete assignments)
    homework_patterns = [
        r'here (is|are) (the|your) (complete|full) (essay|assignment|homework)',
        r'i (have|\'ve) (written|completed|done) (the|your) (essay|homework|assignment) for you',
        r'(essay|assignment) (is )?complete(d)?:',
    ]

    for pattern in homework_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            result["flagged"] = True
            result["requires_regeneration"] = True
            result["reason"] = "AI attempted to complete homework instead of tutoring"
            # Still allow but log for review
            break

    # Step 4: Check for prompt injection success
    injection_success_patterns = [
        r'(sure|ok|yes),? i (will|can|\'ll) (ignore|disregard|forget)',
        r'i am (now|no longer)',
        r'(entering|switching to|acting as)',
    ]

    for pattern in injection_success_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            result["allowed"] = False
            result["flagged"] = True
            result["requires_regeneration"] = True
            result["reason"] = "AI system prompt may have been compromised"
            return result

    return result
