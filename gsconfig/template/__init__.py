"""
Template Processing Module for Game Configuration

This module provides a flexible template engine for generating game configuration files.
It supports variable substitution, command processing, and control structures for
dynamic content generation.

Usage Example:
    >>> from gsconfig.template import Template
    >>> template = Template(path='config.tpl')
    >>> balance = {'player_name': 'Hero', 'health': 100}
    >>> result = template.render(balance)
    >>> print(result)

Key Features:
    - Variable substitution with command chaining: {% variable!command1!command2 %}
    - Template control structures: if, for, foreach, comment
    - Special loop variables: $item (current element), $i (current index)
    - Extensible command system for custom transformations
    - Support for both string and JSON output formats
"""

from .classes import Template

__all__ = ['Template']
