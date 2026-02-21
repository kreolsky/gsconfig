# Refactoring Plan: Splitting `gsconfig/template.py` into a Package

## 1. Executive Summary
The `gsconfig/template.py` module has grown into a monolithic file (~1,000 lines) containing constants, regex patterns, command handlers, and the core `Template` engine. This refactoring aims to split it into a structured package `gsconfig/template/` to improve maintainability, testability, and separation of concerns.

### Goals
- Decompose the monolith into logical sub-modules.
- Maintain full backward compatibility for existing users of `gsconfig.template.Template`.
- Clarify the interface between the template engine and its command handlers.
- Reduce redundancy and improve code readability.

---

## 2. Detailed File-by-File Breakdown

### `gsconfig/template/base.py`
**Purpose**: Centralized storage for constants, regex patterns, and low-level utilities.
- **Constants**: `DEFAULT_COMMAND_LETTER`, `VARIABLE_START/END`, `COMMENT_START/END`, `VAR_ITEM`, `VAR_INDEX`.
- **Regex Patterns**: `RE_COMMAND_NAME`, `RE_PARAM_VALUE`, `RE_VARIABLE_PATTERN`, `RE_COMMENT_PATTERN`, `RE_TEMPLATE_COMMAND_PATTERN`, `RE_KEY_COMMAND_WITH_PARAM`, `RE_COMMAND_IN_VARIABLE`.
- **Utilities**: 
    - `get_special_var_with_commands_regex(var_name)` (Lines 330-335)
    - `remove_trailing_comma(result)` (Lines 512-521)

### `gsconfig/template/handlers.py`
**Purpose**: Transformation logic for both key commands and template control structures.
- **Key Command Handlers**:
    - `key_command_extract` (Lines 342-353)
    - `key_command_wrap` (Lines 355-367)
    - `key_command_list` (Lines 369-375)
    - `key_command_string` (Lines 377-387)
    - `key_command_none` (Lines 389-397)
    - `key_command_get_by_index` (Lines 399-421)
- **Template Command Handlers**:
    - `template_command_if` (Lines 482-495)
    - `template_command_comment` (Lines 498-510)
    - `template_command_foreach` (Lines 523-561)
    - `template_command_for` (Lines 563-603)
- **Internal Logic**:
    - `apply_key_commands_to_value` (Lines 427-449)
    - `process_special_variable_with_commands` (Lines 451-480)

### `gsconfig/template/engine.py`
**Purpose**: The core `Template` class and its orchestration logic.
- **Class**: `Template` (Lines 609-1014)
- **Internal Methods**:
    - `_process_template_comments`
    - `_process_template_commands`
    - `_process_key_commands_pipeline`
    - `_process_key_commands`

### `gsconfig/template/__init__.py`
**Purpose**: Public API exposure and backward compatibility.
- **Exports**:
    ```python
    from .engine import Template
    # Re-export constants if they were used externally
    from .base import (
        DEFAULT_COMMAND_LETTER,
        VARIABLE_START,
        VARIABLE_END,
        # ... other constants
    )
    ```

---

## 3. Step-by-Step Migration Process

### Phase 1: Preparation
1. Create the directory structure: `mkdir -p gsconfig/template/`.
2. Create empty `__init__.py` in the new directory.

### Phase 2: Extraction
1. **Extract Base**: Copy constants and regex to `gsconfig/template/base.py`.
2. **Extract Handlers**: Copy all `key_command_*` and `template_command_*` functions to `gsconfig/template/handlers.py`.
3. **Extract Engine**: Copy the `Template` class to `gsconfig/template/engine.py`.

### Phase 3: Wiring
1. Update imports in `handlers.py` to pull from `.base`.
2. Update imports in `engine.py` to pull from `.base` and `.handlers`.
3. Update `gsconfig/template/__init__.py` to export `Template`.

### Phase 4: Cleanup & Verification
1. Update `gsconfig/__init__.py` to ensure it still points to the correct `Template` location (it should work without changes if `__init__.py` is correct).
2. Run tests to ensure no regressions.
3. Remove the original `gsconfig/template.py`.

---

## 4. Risk Assessment and Mitigation

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Broken Imports** | High | Use `gsconfig/template/__init__.py` to re-export all public symbols. |
| **Circular Dependencies** | Medium | Ensure `handlers.py` does not import from `engine.py`. Pass handlers as arguments to `Template` methods. |
| **Fragile Regex** | Medium | Keep regex patterns exactly as they are in `base.py`. Add unit tests specifically for regex matching. |
| **Lost Documentation** | Low | Ensure all docstrings are preserved during the move. |

---

## 5. Testing Strategy

### Backward Compatibility Check
- Verify `from gsconfig.template import Template` still works.
- Verify `from gsconfig import Template` still works.

### Functional Testing
- Execute `examples/template.ipynb` to verify end-to-end rendering.
- Create a new test script that exercises:
    - Chained key commands (e.g., `!float!int`).
    - Nested template commands (e.g., `if` inside `foreach`).
    - Custom command registration via `Template.register_key_command`.

---

## 6. Dependencies and Import Changes

### `gsconfig/template/handlers.py`
```python
import re
import json
from .base import (
    RE_KEY_COMMAND_WITH_PARAM,
    RE_COMMAND_IN_VARIABLE,
    VAR_ITEM,
    VAR_INDEX,
    get_special_var_with_commands_regex,
    remove_trailing_comma
)
```

### `gsconfig/template/engine.py`
```python
import os
import json
import re
from ..json_handler import JSONHandler
from .base import (
    RE_VARIABLE_PATTERN,
    RE_COMMENT_PATTERN,
    RE_TEMPLATE_COMMAND_PATTERN,
    DEFAULT_COMMAND_LETTER,
    RE_PARAM_VALUE
)
from .handlers import (
    key_command_string,
    key_command_extract,
    key_command_wrap,
    key_command_list,
    key_command_none,
    key_command_get_by_index,
    template_command_if,
    template_command_comment,
    template_command_foreach,
    template_command_for
)
```

---

## 7. Implementation Phases

1. **Phase 1: Scaffolding** - Create directory and `base.py`.
2. **Phase 2: Logic Migration** - Move handlers and engine.
3. **Phase 3: Integration** - Set up `__init__.py` and verify imports.
4. **Phase 4: Validation** - Run full test suite and cleanup.
