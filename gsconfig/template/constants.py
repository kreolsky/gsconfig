"""
Template Processing Module for Game Configuration

This module provides a flexible template engine for generating game configuration files.
It supports variable substitution, command processing, and control structures for
dynamic content generation.

Main Components:
    - Constants: Delimiters, special variables, and regex patterns for template parsing
    - Key Command Handlers: Functions that transform values (e.g., !float, !int, !string)
    - Template Command Handlers: Control structures (if, for, foreach, comment)
    - Template Class: Main class for loading, processing, and rendering templates

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

import os
import json
import re

from ..json_handler import JSONHandler


# CONSTANTS

# Command delimiters and special characters

DEFAULT_COMMAND_LETTER = '!'
"""
Default character used to separate a variable name from its commands.

This character is used to delimit commands in template variables. When a variable
needs to be processed through one or more commands, they are appended to the
variable name using this character.

Example:
    Template: {% player_score!float!int %}
    Here, '!' separates the variable 'player_score' from commands 'float' and 'int'

Usage:
    Can be customized when creating a Template instance, though '!' is the standard
    convention throughout the codebase.
"""

VARIABLE_START = '{%'
"""
Opening delimiter for template variables and commands.

This marker indicates the beginning of a template variable or control structure.
All variables and template commands must be enclosed between VARIABLE_START and
VARIABLE_END delimiters.

Example:
    {% player_name %}
    {% if condition %} content {% endif %}
"""

VARIABLE_END = '%}'
"""
Closing delimiter for template variables and commands.

This marker indicates the end of a template variable or control structure.
It must properly close all VARIABLE_START delimiters.

Example:
    {% player_name %}  - Variable substitution
    {% foreach items %} {{ $item }} {% endforeach %}  - Loop structure
"""

COMMENT_START = '{#'
"""
Opening delimiter for template comments.

This marker indicates the beginning of a comment in the template. Comments are
completely removed during template processing and do not appear in the final output.

Example:
    {# This is a comment that will be removed #}
    {% player_name %}  {# Player's display name #}
"""

COMMENT_END = '#}'
"""
Closing delimiter for template comments.

This marker indicates the end of a comment in the template. All text between
COMMENT_START and COMMENT_END is removed during processing.

Example:
    {# This comment spans multiple lines
       and will be completely removed #}
    {% player_name %}
"""

# Special variables for loops

VAR_ITEM = '$item'
"""
Special variable representing the current item in a foreach loop.

This variable is automatically set to the current element being processed in
a foreach loop. It can be used with commands for transformation.

Example:
    Template: {% foreach items %} value: {% $item!string %}, {% endforeach %}
    Balance: {'items': ['apple', 'banana', 'cherry']}
    Output: value: "apple", value: "banana", value: "cherry"

Note:
    This variable is only valid within the scope of a foreach loop.
"""

VAR_INDEX = '$i'
"""
Special variable representing the current index in a for loop.

This variable is automatically set to the current iteration index (0-based) in
a for loop. It can be used with commands for transformation.

Example:
    Template: {% for count %} iteration: {% $i!int %} {% endfor %}
    Balance: {'count': 3}
    Output: iteration: 0 iteration: 1 iteration: 2

Note:
    This variable is only valid within the scope of a for loop.
"""

# Regex components

RE_COMMAND_NAME = r'[a-zA-Z0-9_]+'
"""
Regular expression pattern for matching valid command names.

This pattern matches one or more alphanumeric characters or underscores, which
constitutes a valid command name in the template system.

Matches:
    - 'float' - Valid command name
    - 'my_command' - Valid command name
    - 'cmd123' - Valid command name

Does not match:
    - 'my-command' - Hyphens are not allowed
    - 'my command' - Spaces are not allowed

Usage:
    Used as a building block in more complex regex patterns for command parsing.
"""

RE_PARAM_VALUE = r'\d+'
"""
Regular expression pattern for matching numeric parameter values.

This pattern matches one or more digits, used for extracting numeric parameters
from commands that require them (e.g., get_0, get_1, get_2).

Matches:
    - '0' - Single digit
    - '123' - Multiple digits

Does not match:
    - '-1' - Negative numbers
    - '1.5' - Decimal numbers
    - 'abc' - Non-numeric values

Usage:
    Used in commands like get_N where N is a numeric index.
"""

# Compiled or raw regex patterns

RE_VARIABLE_PATTERN = r'\{%\s*([a-zA-Z0-9_!]+)\s*%\}'
"""
Regular expression pattern for matching template variables.

This pattern matches template variables enclosed in {% %} delimiters, capturing
the variable name and any commands. The captured group includes the variable name
and optional commands separated by the command letter.

Matches:
    - {% player_name %} - Simple variable
    - {% score!float %} - Variable with command
    - {% data!get_0!string %} - Variable with multiple commands

Captured Group:
    Group 1: The variable name and commands (e.g., 'player_name', 'score!float')

Usage:
    Used to find all variables in a template that need to be replaced with values
    from the balance dictionary.

Example:
    >>> import re
    >>> pattern = re.compile(RE_VARIABLE_PATTERN)
    >>> template = "Name: {% player_name %}, Score: {% score!float %}"
    >>> matches = pattern.findall(template)
    >>> matches
    ['player_name', 'score!float']
"""

RE_COMMENT_PATTERN = r'\{\#\s*(.*?)\s*\#\}\n{0,1}'
"""
Regular expression pattern for matching template comments.

This pattern matches comments enclosed in {# #} delimiters, optionally followed
by a newline character. The captured group contains the comment content.

Matches:
    - {# This is a comment #} - Simple comment
    - {# Multi-line\ncomment #} - Multi-line comment (with DOTALL flag)
    - {# Comment #}\n - Comment with trailing newline

Captured Group:
    Group 1: The comment content without delimiters

Usage:
    Used to remove all comments from the template before processing.

Example:
    >>> import re
    >>> pattern = re.compile(RE_COMMENT_PATTERN, re.DOTALL)
    >>> template = "Name: {% player %} {# Player name #}"
    >>> result = pattern.sub('', template)
    >>> result
    'Name: {% player %} '
"""

RE_TEMPLATE_COMMAND_PATTERN = r'(\{%\s*([\w_]+)\s+([\w_]*)\s*%\}(.*?)\{%\s*end\2\s*%\}\n{0,1})'
"""
Regular expression pattern for matching template control structure commands.

This pattern matches template commands with opening and closing tags, capturing
the command name, parameters, and content. It supports nested command structures.

Matches:
    - {% if condition %} content {% endif %} - Conditional block
    - {% foreach items %} {{ $item }} {% endforeach %} - Loop block
    - {% for count %} iteration {{ $i }} {% endfor %} - Counted loop

Captured Groups:
    Group 1: Full match including opening and closing tags
    Group 2: Command name (e.g., 'if', 'foreach', 'for')
    Group 3: Parameters (e.g., 'condition', 'items', 'count')
    Group 4: Content between opening and closing tags

Usage:
    Used to process template control structures before variable substitution.

Example:
    >>> import re
    >>> pattern = re.compile(RE_TEMPLATE_COMMAND_PATTERN, re.DOTALL)
    >>> template = "{% if show %}Hello{% endif %}"
    >>> matches = pattern.findall(template)
    >>> matches[0][1]  # Command name
    'if'
    >>> matches[0][2]  # Parameters
    'show'
    >>> matches[0][3]  # Content
    'Hello'
"""

RE_KEY_COMMAND_WITH_PARAM = r'_(\d+)'
"""
Regular expression pattern for matching key commands with numeric parameters.

This pattern matches commands that include a numeric parameter, such as get_N
or extract_N, where N is a number.

Matches:
    - '_0' - Parameter value 0
    - '_123' - Parameter value 123

Captured Group:
    Group 1: The numeric parameter value

Usage:
    Used to extract the parameter from commands like get_0, get_1, etc.

Example:
    >>> import re
    >>> pattern = re.compile(RE_KEY_COMMAND_WITH_PARAM)
    >>> command = 'get_2'
    >>> match = pattern.search(command)
    >>> match.group(1)
    '2'
"""

RE_COMMAND_IN_VARIABLE = r'!([a-zA-Z0-9_]+)'
"""
Regular expression pattern for matching commands within a variable expression.

This pattern matches individual commands that are chained to a variable name,
separated by the command letter (!).

Matches:
    - '!float' - Command to convert to float
    - '!string' - Command to wrap in quotes
    - '!get_0' - Command to get element at index 0

Captured Group:
    Group 1: The command name (without the ! prefix)

Usage:
    Used to extract all commands from a variable expression for sequential processing.

Example:
    >>> import re
    >>> pattern = re.compile(RE_COMMAND_IN_VARIABLE)
    >>> variable = 'data!get_0!string'
    >>> commands = pattern.findall(variable)
    >>> commands
    ['get_0', 'string']
"""


# Helper to generate regex for special variables with commands
def get_special_var_with_commands_regex(var_name):
    """
    Generates a regex pattern to match a special variable with one or more commands.
    Example: {% $item!cmd1!cmd2 %}
    """
    return r'\{%\s*' + re.escape(var_name) + r'(!' + RE_COMMAND_NAME + r')+\s*%\}'


def remove_trailing_comma(result):
    """
    Удаляет последнюю запятую из строки, если она присутствует.
    
    :param result: Строка, из которой необходимо удалить последнюю запятую.
    :return: Строка без последней запятой.
    """
    if result.strip().endswith('},'):
        return result.strip().strip(",")
    return result
