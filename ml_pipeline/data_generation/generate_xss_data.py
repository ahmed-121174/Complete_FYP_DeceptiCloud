#!/usr/bin/env python3
"""
XSS Dataset Generator
Generates synthetic XSS payloads and benign inputs for training
"""

import random
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# XSS Payload Templates (from OWASP and common patterns)
XSS_PAYLOADS = [
    # Basic script tags
    "<script>alert(1)</script>",
    "<script>alert('XSS')</script>",
    "<script>alert(document.cookie)</script>",
    "<script>alert(document.domain)</script>",
    "<script>prompt(1)</script>",
    "<script>confirm(1)</script>",
    
    # Event handlers
    "<img src=x onerror=alert(1)>",
    "<img src=x onerror=alert('XSS')>",
    "<body onload=alert(1)>",
    "<input onfocus=alert(1) autofocus>",
    "<select onfocus=alert(1) autofocus>",
    "<textarea onfocus=alert(1) autofocus>",
    "<iframe onload=alert(1)>",
    "<svg onload=alert(1)>",
    "<marquee onstart=alert(1)>",
    
    # Without quotes
    "<script>alert(String.fromCharCode(88,83,83))</script>",
    "<img src=x onerror=alert(String.fromCharCode(88,83,83))>",
    
    # Case variations
    "<ScRiPt>alert(1)</ScRiPt>",
    "<SCRIPT>alert(1)</SCRIPT>",
    "<sCrIpT>alert(1)</sCrIpT>",
    
    # With encoding
    "<script>alert&#40;1&#41;</script>",
    "<script>alert&#x28;1&#x29;</script>",
    "%3Cscript%3Ealert(1)%3C/script%3E",
    
    # SVG-based
    "<svg><script>alert(1)</script></svg>",
    "<svg/onload=alert(1)>",
    "<svg><animate onbegin=alert(1)>",
    
    # JavaScript protocol
    "javascript:alert(1)",
    "javascript:alert('XSS')",
    "javascript:void(alert(1))",
    
    # Data protocol
    "data:text/html,<script>alert(1)</script>",
    "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
    
    # With HTML entities
    "&lt;script&gt;alert(1)&lt;/script&gt;",
    "&#60;script&#62;alert(1)&#60;/script&#62;",
    
    # Obfuscated
    "<script>eval(atob('YWxlcnQoMSk='))</script>",
    "<script>eval(String.fromCharCode(97,108,101,114,116,40,49,41))</script>",
    
    # With comments
    "<script>/**/alert(1)/**/</script>",
    "<script><!--alert(1)--></script>",
    
    # Multiple tags
    "<script><script>alert(1)</script>",
    "</script><script>alert(1)</script>",
    
    # With attributes
    "<img src='x' onerror='alert(1)'>",
    '<img src="x" onerror="alert(1)">',
    "<img src=`x` onerror=`alert(1)`>",
    
    # Form-based
    "<form action=javascript:alert(1)><input type=submit>",
    "<button formaction=javascript:alert(1)>",
    
    # Link-based
    "<a href=javascript:alert(1)>click</a>",
    "<a href='javascript:alert(1)'>click</a>",
    
    # Meta refresh
    "<meta http-equiv='refresh' content='0;url=javascript:alert(1)'>",
    
    # Object/embed
    "<object data=javascript:alert(1)>",
    "<embed src=javascript:alert(1)>",
]

# Benign input patterns
BENIGN_PATTERNS = [
    # Normal search queries
    "hello world",
    "python programming",
    "machine learning tutorial",
    "how to cook pasta",
    "weather forecast",
    "news today",
    "best restaurants near me",
    "movie recommendations",
    
    # Normal form inputs
    "john.doe@example.com",
    "John Doe",
    "123 Main Street",
    "+1-555-0123",
    "New York, NY 10001",
    
    # Normal URLs
    "https://example.com",
    "http://www.google.com",
    "https://github.com/user/repo",
    
    # Normal HTML (escaped)
    "&lt;p&gt;Hello World&lt;/p&gt;",
    "&lt;div&gt;Content&lt;/div&gt;",
    "&lt;a href='link'&gt;Click&lt;/a&gt;",
    
    # Numbers and dates
    "12345",
    "2026-04-18",
    "10:30 AM",
    "$99.99",
    
    # Special characters (but not XSS)
    "user@domain.com",
    "C:\\Users\\Documents",
    "/home/user/file.txt",
    "price: $50-$100",
    
    # Code snippets (properly escaped)
    "function test() { return true; }",
    "SELECT * FROM users WHERE id=1",
    "print('Hello World')",
    
    # Questions
    "What is the capital of France?",
    "How do I reset my password?",
    "Where can I find help?",
    
    # Commands (not XSS)
    "ls -la",
    "cd /home",
    "git commit -m 'update'",
]

def mutate_xss_payload(payload):
    """Apply mutations to XSS payload for variation"""
    mutations = []
    
    # Original
    mutations.append(payload)
    
    # Add whitespace
    mutations.append(payload.replace('<', '< ').replace('>', ' >'))
    mutations.append(payload.replace('=', ' = '))
    
    # Case variations
    mutations.append(payload.upper())
    mutations.append(payload.lower())
    mutations.append(''.join(c.upper() if i % 2 else c.lower() for i, c in enumerate(payload)))
    
    # Add null bytes (simulated)
    mutations.append(payload.replace('<', '<\x00'))
    
    # Double encoding
    mutations.append(payload.replace('<', '%253C').replace('>', '%253E'))
    
    # Add comments
    mutations.append(payload.replace('alert', '/**/alert/**/'))
    
    # Add line breaks
    mutations.append(payload.replace('>', '>\n'))
    
    return mutations

def mutate_benign_input(text):
    """Apply variations to benign input"""
    mutations = []
    
    # Original
    mutations.append(text)
    
    # Case variations
    mutations.append(text.upper())
    mutations.append(text.lower())
    mutations.append(text.title())
    
    # Add punctuation
    mutations.append(text + '.')
    mutations.append(text + '!')
    mutations.append(text + '?')
    
    # Add quotes
    mutations.append(f'"{text}"')
    mutations.append(f"'{text}'")
    
    # Add spaces
    mutations.append(' ' + text + ' ')
    mutations.append(text.replace(' ', '  '))
    
    return mutations

def generate_xss_dataset(num_samples=5000):
    """Generate XSS dataset with equal benign and malicious samples"""
    dataset = []
    
    # Generate malicious samples (50%)
    num_malicious = num_samples // 2
    print(f"Generating {num_malicious} malicious XSS samples...")
    
    for i in range(num_malicious):
        # Pick random payload
        base_payload = random.choice(XSS_PAYLOADS)
        
        # Apply mutations
        mutations = mutate_xss_payload(base_payload)
        payload = random.choice(mutations)
        
        dataset.append({
            'text': payload,
            'label': 1,  # Malicious
            'type': 'xss'
        })
    
    # Generate benign samples (50%)
    num_benign = num_samples - num_malicious
    print(f"Generating {num_benign} benign samples...")
    
    for i in range(num_benign):
        # Pick random benign pattern
        base_text = random.choice(BENIGN_PATTERNS)
        
        # Apply mutations
        mutations = mutate_benign_input(base_text)
        text = random.choice(mutations)
        
        dataset.append({
            'text': text,
            'label': 0,  # Benign
            'type': 'benign'
        })
    
    # Shuffle dataset
    random.shuffle(dataset)
    
    return dataset

def save_dataset(dataset, output_path):
    """Save dataset to JSON file"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(dataset, f, indent=2)
    
    print(f"Dataset saved to {output_path}")
    print(f"Total samples: {len(dataset)}")
    print(f"Malicious: {sum(1 for d in dataset if d['label'] == 1)}")
    print(f"Benign: {sum(1 for d in dataset if d['label'] == 0)}")

if __name__ == '__main__':
    # Generate dataset
    dataset = generate_xss_dataset(num_samples=5000)
    
    # Save to file
    output_path = Path(__file__).parent.parent / 'data' / 'xss_dataset.json'
    save_dataset(dataset, output_path)
    
    # Print sample
    print("\nSample malicious:")
    malicious = [d for d in dataset if d['label'] == 1][:3]
    for sample in malicious:
        print(f"  {sample['text'][:80]}...")
    
    print("\nSample benign:")
    benign = [d for d in dataset if d['label'] == 0][:3]
    for sample in benign:
        print(f"  {sample['text'][:80]}...")
