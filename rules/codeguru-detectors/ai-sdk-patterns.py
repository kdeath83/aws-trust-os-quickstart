"""
CodeGuru Detectors for AI SDK Patterns
These custom detectors identify AI SDK usage patterns in code for governance.
"""

from aws_codeguru_profiler_python import Detector

# Detector: Direct OpenAI API Key Usage
@Detector(
    name="DirectOpenAIAPIKey",
    description="Detects hardcoded OpenAI API keys in source code",
    severity="HIGH",
    tags=["security", "ai", "secrets"]
)
def detect_openai_api_key(code_line: str, file_path: str) -> bool:
    """
    Detects potential OpenAI API keys in code.
    
    Pattern matches:
    - openai.api_key = "sk-..."
    - os.environ["OPENAI_API_KEY"] = "..."
    - api_key="sk-..."
    """
    import re
    
    patterns = [
        r'openai\.api_key\s*=\s*["\']sk-[a-zA-Z0-9]{48}["\']',
        r'OPENAI_API_KEY\s*=\s*["\']sk-[a-zA-Z0-9]{48}["\']',
        r'api_key\s*=\s*["\']sk-[a-zA-Z0-9]{48}["\']',
    ]
    
    for pattern in patterns:
        if re.search(pattern, code_line):
            return True
    
    return False


# Detector: Anthropic API Key Usage
@Detector(
    name="DirectAnthropicAPIKey",
    description="Detects hardcoded Anthropic API keys in source code",
    severity="HIGH",
    tags=["security", "ai", "secrets"]
)
def detect_anthropic_api_key(code_line: str, file_path: str) -> bool:
    """Detects potential Anthropic API keys."""
    import re
    
    patterns = [
        r'anthropic\.api_key\s*=\s*["\']sk-ant-[a-zA-Z0-9_-]+["\']',
        r'ANTHROPIC_API_KEY\s*=\s*["\']sk-ant-[a-zA-Z0-9_-]+["\']',
    ]
    
    for pattern in patterns:
        if re.search(pattern, code_line):
            return True
    
    return False


# Detector: Bedrock SDK Usage (Good Pattern)
@Detector(
    name="BedrockSDKUsage",
    description="Identifies AWS Bedrock SDK usage for governance tracking",
    severity="INFO",
    tags=["ai", "governance", "bedrock"]
)
def detect_bedrock_usage(code_line: str, file_path: str) -> bool:
    """
    Detects Bedrock SDK usage patterns.
    This is a positive indicator for AI governance.
    """
    patterns = [
        'boto3.client("bedrock-runtime"',
        'boto3.client("bedrock"',
        'bedrock_runtime.invoke_model',
        'bedrock.apply_guardrail',
        'from langchain_aws import Bedrock',
    ]
    
    for pattern in patterns:
        if pattern in code_line:
            return True
    
    return False


# Detector: Unprotected AI Model Invocation
@Detector(
    name="UnprotectedAIModelInvocation",
    description="Detects AI model calls without guardrails or safety checks",
    severity="MEDIUM",
    tags=["ai", "safety", "guardrails"]
)
def detect_unprotected_invocation(code_lines: list, file_path: str) -> dict:
    """
    Detects AI model invocations that lack protective measures.
    
    Checks for:
    - Missing input validation
    - No output filtering
    - No audit logging
    - Direct API calls without abstraction
    """
    import re
    
    ai_invoke_patterns = [
        r'openai\.ChatCompletion\.create\(',
        r'anthropic\.Client\(\.\.\.\)\.completion\(',
        r'\.invoke_model\(',
        r'\.converse\(',
    ]
    
    protection_patterns = [
        'guardrail',
        'filter',
        'validate',
        'sanitize',
        'audit',
        'log',
    ]
    
    results = []
    
    for i, line in enumerate(code_lines):
        for pattern in ai_invoke_patterns:
            if re.search(pattern, line):
                # Check surrounding lines for protection
                context_start = max(0, i - 5)
                context_end = min(len(code_lines), i + 5)
                context = '\n'.join(code_lines[context_start:context_end])
                
                has_protection = any(p in context.lower() for p in protection_patterns)
                
                if not has_protection:
                    results.append({
                        'line': i + 1,
                        'code': line.strip(),
                        'issue': 'Unprotected AI model invocation'
                    })
    
    return {
        'detected': len(results) > 0,
        'findings': results
    }


# Detector: Insecure AI Output Handling
@Detector(
    name="InsecureAIOutputHandling",
    description="Detects AI model outputs used without validation",
    severity="HIGH",
    tags=["security", "ai", "injection"]
)
def detect_insecure_output_handling(code_lines: list, file_path: str) -> dict:
    """
    Detects cases where AI model output is used unsafely.
    
    Risky patterns:
    - Direct SQL query construction
    - Shell command execution
    - HTML rendering without escaping
    - eval() or exec() on AI output
    """
    import re
    
    dangerous_patterns = [
        (r'cursor\.execute\([^)]*%s', 'SQL injection risk'),
        (r'os\.system\([^)]*\+', 'Command injection risk'),
        (r'subprocess\.call\([^)]*\+', 'Command injection risk'),
        (r'eval\([^)]*\)', 'Code injection risk'),
        (r'exec\([^)]*\)', 'Code injection risk'),
        (r'\.innerHTML\s*=', 'XSS risk'),
        (r'dangerouslySetInnerHTML', 'XSS risk'),
    ]
    
    # Find where AI response is assigned
    ai_response_vars = []
    for i, line in enumerate(code_lines):
        if re.search(r'(response|completion|output|result)\s*=.*(?:invoke_model|ChatCompletion|completion)', line):
            var_name = line.split('=')[0].strip()
            ai_response_vars.append(var_name)
    
    results = []
    
    for i, line in enumerate(code_lines):
        for var in ai_response_vars:
            if var in line:
                for pattern, risk in dangerous_patterns:
                    if re.search(pattern, line):
                        results.append({
                            'line': i + 1,
                            'code': line.strip(),
                            'risk': risk,
                            'variable': var
                        })
    
    return {
        'detected': len(results) > 0,
        'findings': results
    }


# Detector: Missing Error Handling for AI Calls
@Detector(
    name="MissingAIErrorHandling",
    description="Detects AI API calls without proper exception handling",
    severity="MEDIUM",
    tags=["reliability", "ai", "exceptions"]
)
def detect_missing_error_handling(code_lines: list, file_path: str) -> dict:
    """Detects AI API calls that aren't wrapped in try-except blocks."""
    import re
    
    ai_patterns = [
        r'\.invoke_model\(',
        r'\.converse\(',
        r'openai\.\w+\.create\(',
        r'anthropic\.\w+\(',
    ]
    
    results = []
    in_try_block = False
    
    for i, line in enumerate(code_lines):
        # Track try/except blocks (simplified)
        if 'try:' in line:
            in_try_block = True
        elif 'except' in line or 'finally:' in line:
            in_try_block = False
        
        for pattern in ai_patterns:
            if re.search(pattern, line) and not in_try_block:
                results.append({
                    'line': i + 1,
                    'code': line.strip(),
                    'issue': 'AI API call without error handling'
                })
    
    return {
        'detected': len(results) > 0,
        'findings': results
    }


# Detector: PII in Prompts
@Detector(
    name="PIIInPrompts",
    description="Detects potential PII being sent to AI models",
    severity="HIGH",
    tags=["privacy", "ai", "pii"]
)
def detect_pii_in_prompts(code_lines: list, file_path: str) -> dict:
    """
    Detects potential PII being included in AI prompts.
    
    Patterns:
    - Email addresses
    - Phone numbers
    - SSN patterns
    - Credit card patterns
    """
    import re
    
    pii_patterns = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'Email address'),
        (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN'),
        (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 'Credit card'),
        (r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', 'Phone number'),
    ]
    
    prompt_patterns = [
        r'messages\s*=\s*\[',
        r'prompt\s*=\s*["\']',
        r'content\s*=\s*["\']',
    ]
    
    results = []
    in_prompt = False
    prompt_start = 0
    
    for i, line in enumerate(code_lines):
        # Detect prompt start
        for pattern in prompt_patterns:
            if re.search(pattern, line):
                in_prompt = True
                prompt_start = i
                break
        
        # Detect prompt end (simplified)
        if in_prompt and (line.strip().endswith(']') or line.strip().endswith(')')):
            in_prompt = False
        
        if in_prompt:
            for pii_pattern, pii_type in pii_patterns:
                if re.search(pii_pattern, line):
                    results.append({
                        'line': i + 1,
                        'code': line.strip(),
                        'pii_type': pii_type
                    })
    
    return {
        'detected': len(results) > 0,
        'findings': results
    }


# Detector: Model Version Pinning
@Detector(
    name="UnpinnedModelVersion",
    description="Detects AI model calls without version pinning",
    severity="LOW",
    tags=["ai", "reliability", "versioning"]
)
def detect_unpinned_model(code_line: str, file_path: str) -> bool:
    """Detects model calls that don't specify a version."""
    import re
    
    # Look for model IDs without versions
    unpinned_patterns = [
        r'model\s*=\s*["\']gpt-4["\']',
        r'model\s*=\s*["\']claude-3-sonnet["\']',
        r'modelId\s*=\s*["\']anthropic\.claude-3-sonnet["\']',
    ]
    
    version_patterns = [
        r'-\d{8}',  # Date version format
        r'v\d+\.\d+',  # Semantic version
    ]
    
    for pattern in unpinned_patterns:
        if re.search(pattern, code_line):
            # Check if version is present
            if not any(re.search(v, code_line) for v in version_patterns):
                return True
    
    return False


# Configuration for CodeGuru Reviewer
def get_codeguru_config():
    """Return CodeGuru Reviewer configuration for AI Trust OS."""
    return {
        "detectors": [
            "DirectOpenAIAPIKey",
            "DirectAnthropicAPIKey",
            "BedrockSDKUsage",
            "UnprotectedAIModelInvocation",
            "InsecureAIOutputHandling",
            "MissingAIErrorHandling",
            "PIIInPrompts",
            "UnpinnedModelVersion"
        ],
        "severity_threshold": "MEDIUM",
        "include_recommendations": True,
        "scan_scope": {
            "include": ["*.py", "*.js", "*.ts", "*.java", "*.go"],
            "exclude": ["test_*", "*_test.py", "*.spec.js"]
        }
    }
