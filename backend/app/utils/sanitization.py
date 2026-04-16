"""
Input Sanitization Utilities

Provides functions to sanitize user input and prevent:
- XSS (Cross-Site Scripting) attacks
- SQL Injection (additional layer beyond ORM)
- HTML injection
- Path traversal attacks
"""

import re
import html
from typing import Optional, Any
from urllib.parse import quote


# HTML/XSS SANITIZATION


def sanitize_html(text: str, allow_basic_formatting: bool = False) -> str:
    """
    Sanitize HTML to prevent XSS attacks

    Args:
        text: Input text that may contain HTML
        allow_basic_formatting: If True, allows <b>, <i>, <u> tags

    Returns:
        Sanitized text

    Examples:
        >>> sanitize_html("<script>alert('XSS')</script>Hello")
        "&lt;script&gt;alert('XSS')&lt;/script&gt;Hello"

        >>> sanitize_html("<b>Bold</b> text", allow_basic_formatting=True)
        "<b>Bold</b> text"
    """
    if not text:
        return text

    if allow_basic_formatting:
        # Allow only safe tags
        safe_tags = ["b", "i", "u", "strong", "em"]

        # Escape everything first
        sanitized = html.escape(text)

        # Un-escape safe tags
        for tag in safe_tags:
            sanitized = sanitized.replace(f"&lt;{tag}&gt;", f"<{tag}>")
            sanitized = sanitized.replace(f"&lt;/{tag}&gt;", f"</{tag}>")

        return sanitized
    else:
        # Escape all HTML
        return html.escape(text)


def strip_html(text: str) -> str:
    """
    Remove all HTML tags from text

    Args:
        text: Input text with HTML tags

    Returns:
        Plain text without HTML

    Examples:
        >>> strip_html("<p>Hello <b>World</b></p>")
        "Hello World"
    """
    if not text:
        return text

    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)

    # Decode HTML entities
    clean = html.unescape(clean)

    return clean.strip()


# Script injection prevention


def sanitize_script_content(text: str) -> str:
    """
    Remove potentially dangerous script content

    Args:
        text: Input text

    Returns:
        Text with script content removed

    Examples:
        >>> sanitize_script_content("Hello <script>alert(1)</script>")
        "Hello "
    """
    if not text:
        return text

    # Remove script tags and content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove event handlers (onclick, onerror, etc.)
    text = re.sub(r'\bon\w+\s*=\s*["\'].*?["\']', '', text, flags=re.IGNORECASE)

    # Remove javascript: URLs
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)

    return text


# SQL INJECTION PREVENTION (Additional Layer)


def sanitize_sql_string(text: str) -> str:
    """
    Additional SQL injection protection

    Note: This is a secondary defense. Primary defense is parameterized
    queries via SQLAlchemy ORM.

    Args:
        text: Input text

    Returns:
        Sanitized text

    Examples:
        >>> sanitize_sql_string("'; DROP TABLE users; --")
        "'; DROP TABLE users; --"  # ORM will handle properly
    """
    if not text:
        return text

    # Remove null bytes
    text = text.replace('\x00', '')

    # Remove SQL comments
    text = re.sub(r'--[^\n]*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    return text


# Path traversal prevention


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal

    Args:
        filename: User-provided filename

    Returns:
        Safe filename

    Examples:
        >>> sanitize_filename("../../etc/passwd")
        "passwd"

        >>> sanitize_filename("file<>.txt")
        "file.txt"
    """
    if not filename:
        return filename

    # Remove path separators
    filename = filename.replace('/', '').replace('\\', '')

    # Remove parent directory references
    filename = filename.replace('..', '')

    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*]', '', filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')

    return filename or 'file'


# URL sanitization


def sanitize_url(url: str, allow_schemes: Optional[list[str]] = None) -> str:
    """
    Sanitize URL to prevent malicious redirects

    Args:
        url: User-provided URL
        allow_schemes: List of allowed URL schemes (default: ['http', 'https'])

    Returns:
        Sanitized URL

    Examples:
        >>> sanitize_url("javascript:alert(1)")
        ""  # Blocked

        >>> sanitize_url("https://example.com")
        "https://example.com"
    """
    if not url:
        return url

    if allow_schemes is None:
        allow_schemes = ['http', 'https']

    # Check scheme
    if ':' in url:
        scheme = url.split(':', 1)[0].lower()
        if scheme not in allow_schemes:
            return ''  # Block dangerous schemes

    # Remove javascript: and data: URLs
    if url.lower().startswith(('javascript:', 'data:', 'vbscript:')):
        return ''

    return url


# Email sanitization


def sanitize_email(email: str) -> str:
    """
    Sanitize email address

    Args:
        email: User-provided email

    Returns:
        Sanitized email (lowercase, trimmed)

    Examples:
        >>> sanitize_email("  User@Example.COM  ")
        "user@example.com"
    """
    if not email:
        return email

    # Convert to lowercase and trim
    email = email.lower().strip()

    # Basic email format validation
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return ''

    return email


# General text sanitization


def sanitize_text(
    text: str,
    max_length: Optional[int] = None,
    allow_newlines: bool = True,
    allow_unicode: bool = True
) -> str:
    """
    General text sanitization

    Args:
        text: Input text
        max_length: Maximum allowed length
        allow_newlines: Whether to allow newline characters
        allow_unicode: Whether to allow unicode characters

    Returns:
        Sanitized text

    Examples:
        >>> sanitize_text("Hello\\nWorld", max_length=10)
        "Hello\\nWorl"

        >>> sanitize_text("Hello\\nWorld", allow_newlines=False)
        "Hello World"
    """
    if not text:
        return text

    # Remove null bytes
    text = text.replace('\x00', '')

    # Handle newlines
    if not allow_newlines:
        text = text.replace('\n', ' ').replace('\r', ' ')

    # Handle unicode
    if not allow_unicode:
        text = text.encode('ascii', 'ignore').decode('ascii')

    # Remove control characters except newlines and tabs
    if allow_newlines:
        text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t')
    else:
        text = ''.join(char for char in text if char.isprintable() or char == '\t')

    # Trim whitespace
    text = text.strip()

    # Limit length
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


# PYDANTIC VALIDATOR HELPERS


def sanitize_string_field(v: Optional[str]) -> Optional[str]:
    """
    Pydantic validator for sanitizing string fields

    Usage:
        class MySchema(BaseModel):
            description: str

            @field_validator('description')
            @classmethod
            def sanitize_description(cls, v):
                return sanitize_string_field(v)

    Args:
        v: Input value

    Returns:
        Sanitized string or None
    """
    if v is None:
        return None

    if not isinstance(v, str):
        return v

    # Apply sanitization
    v = sanitize_html(v, allow_basic_formatting=False)
    v = sanitize_script_content(v)
    v = sanitize_text(v)

    return v if v else None


# MIDDLEWARE HELPER


class InputSanitizer:
    """
    Class to sanitize all input in a request

    Can be used as a dependency in FastAPI endpoints
    """

    @staticmethod
    def sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
        """
        Recursively sanitize all string values in a dictionary

        Args:
            data: Input dictionary

        Returns:
            Dictionary with sanitized values
        """
        if not isinstance(data, dict):
            return data

        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = sanitize_string_field(value)
            elif isinstance(value, dict):
                sanitized[key] = InputSanitizer.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    InputSanitizer.sanitize_dict(item) if isinstance(item, dict)
                    else sanitize_string_field(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized


# Usage examples

"""
IN PYDANTIC SCHEMAS:
```python
from app.utils.sanitization import sanitize_string_field
from pydantic import BaseModel, field_validator

class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None

    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v):
        return sanitize_string_field(v)
```

IN ENDPOINTS:
```python
from app.utils.sanitization import sanitize_html

@router.post("/teams")
def create_team(team_data: TeamCreate):
    # Additional sanitization if needed
    safe_description = sanitize_html(team_data.description)
    ...
```

AS DEPENDENCY:
```python
from app.utils.sanitization import InputSanitizer

@router.post("/teams")
def create_team(
    team_data: TeamCreate,
    sanitizer: InputSanitizer = Depends()
):
    # All input already sanitized
    ...
```
"""
