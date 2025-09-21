"""Unit tests for utility functions."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from budget_sync.utils import safe_str_cmp


def test_safe_str_cmp_with_strings():
    """
    GIVEN two strings
    WHEN safe_str_cmp is called
    THEN check the comparison is correct
    """
    assert safe_str_cmp("hello", "hello") is True
    assert safe_str_cmp("hello", "world") is False
    assert safe_str_cmp("", "") is True
    assert safe_str_cmp("a", "b") is False

def test_safe_str_cmp_with_bytes():
    """
    GIVEN two byte strings
    WHEN safe_str_cmp is called
    THEN check the comparison is correct
    """
    assert safe_str_cmp(b"hello", b"hello") is True
    assert safe_str_cmp(b"hello", b"world") is False

def test_safe_str_cmp_mixed_types():
    """
    GIVEN mixed string and byte inputs
    WHEN safe_str_cmp is called
    THEN check the comparison is correct
    """
    assert safe_str_cmp("hello", b"hello") is True
    assert safe_str_cmp(b"hello", "hello") is True
    assert safe_str_cmp("hello", b"world") is False

def test_safe_str_cmp_special_characters():
    """
    GIVEN strings with special characters
    WHEN safe_str_cmp is called
    THEN check the comparison handles UTF-8 correctly
    """
    assert safe_str_cmp("héllo", "héllo") is True
    assert safe_str_cmp("héllo", "hello") is False
    assert safe_str_cmp("🐍", "🐍") is True
    assert safe_str_cmp("��", "🐊") is False 