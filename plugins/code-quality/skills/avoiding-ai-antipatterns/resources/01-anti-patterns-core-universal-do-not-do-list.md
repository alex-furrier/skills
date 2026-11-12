# Anti-Patterns Core - Universal "DO NOT DO" List

These patterns are explicitly forbidden across all languages and projects.

## Universal Anti-Patterns

### Silent Failures and Defensive Programming
- **NEVER use silent fallbacks** - Raise loud errors instead
- **NEVER cover edge cases with heuristics** - Fail explicitly and ask for clarification
- **NEVER catch exceptions without re-raising or logging** - Errors should be visible
- **AVOID defensive programming that hides issues** - Make problems obvious

**Why**: Hidden failures lead to debugging nightmares. Explicit errors surface problems immediately.

**Example**:
```python
# L BAD - Silent fallback
def get_config(key):
    return os.getenv(key) or "default_value"

#  GOOD - Loud error
def get_config(key):
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Required environment variable {key} not set")
    return value
```

### Unnecessary Backwards Compatibility Shims
- **DO NOT create re-export shims unless explicitly requested** - Clean breaks are better than complexity
- **DO NOT keep old file locations with imports from new locations** - Just move the code
- **DO NOT add compatibility layers for refactoring** - Update call sites instead

**Why**: Backwards compatibility shims add ongoing maintenance burden, confuse future developers about which is the "real" location, and accumulate technical debt. Unless the user explicitly asks for backwards compatibility (e.g., public API with external consumers), prefer clean refactoring.

**Example**:
```python
# ❌ BAD - Unnecessary re-export shim after renaming/moving
# old_location/utils.py
from new_location.utils import *  # Re-exporting for "compatibility"

# ✅ GOOD - Just move the code and update imports
# Delete old_location/utils.py entirely
# Update all call sites to use new_location.utils

# ❌ BAD - Keeping renamed function with shim
def old_function_name(*args, **kwargs):
    """Deprecated: Use new_function_name instead."""
    return new_function_name(*args, **kwargs)

# ✅ GOOD - Just rename and update call sites
# Remove old_function_name entirely
# Search and replace all usages to new_function_name
```

**When backwards compatibility IS appropriate:**
- Public APIs with external consumers who can't immediately update
- Library code with documented deprecation cycles
- User explicitly requests it with clear reasoning

**Default approach:** Clean breaks with updated call sites, not compatibility shims.

---

## Python Anti-Patterns

### NEVER Use Inline Code
- **NO INLINE IMPORTS** - All imports at module level
  - **Only exception**: Avoiding circular dependencies (which itself is a code smell - fix the architecture)
- **NO NESTED FUNCTIONS** - Define functions at module level unless absolutely necessary
- **NO INLINE CLASS DEFINITIONS** - Classes at module level

**Why**: Makes code harder to test, reuse, and understand. Violates single responsibility. If you need inline imports to avoid circular deps, that's a sign of poor module organization.

**Example**:
```python
# L BAD - Inline imports and nested functions
def process_data():
    import pandas as pd  # NO!

    def helper():  # NO!
        return pd.DataFrame()

    return helper()

#  GOOD - Module-level organization
import pandas as pd

def helper():
    return pd.DataFrame()

def process_data():
    return helper()
```

### Type Safety Anti-Patterns
- **DO NOT use `getattr` for known attributes** - Defeats type hinting purposes
- **DO NOT use `Dict[str, Any]`** - Create dataclasses instead
- **DO NOT use `Any` type hints** - Be specific about types

**Why**: Type hints exist to catch errors at development time. Dynamic attribute access bypasses this safety.

**Example**:
```python
# L BAD - Dynamic attribute access defeats type hints
class Config:
    database_url: str
    api_key: str

config = Config()
db_url = getattr(config, "database_url")  # Type checker can't help here

#  GOOD - Direct attribute access with type safety
db_url = config.database_url  # Type checker validates this exists
```

### Error Handling Philosophy
- **Raise exceptions, don't return None** - Make failures explicit
- **No silent failures** - See global anti-patterns above
- **No "try everything" exception handlers** - Be specific about what you catch

**Example**:
```python
# L BAD - Returns None, caller has to check
def find_user(user_id: int) -> Optional[User]:
    try:
        return db.query(User).filter(User.id == user_id).first()
    except Exception:
        return None

#  GOOD - Raises exception, failure is obvious
def find_user(user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise UserNotFoundError(f"User {user_id} not found")
    return user
```

---

## Testing Anti-Patterns

### Over-Mocking
- **DO NOT mock everything** - Prefer fakes, doubles, and stubs
- **DO NOT create inline mocks** - Put reusable test utilities in conftest.py
- **DO NOT mock what you own** - Only mock external dependencies

**Why**: Over-mocking creates brittle tests that break on refactoring and don't catch real bugs.

**Example**:
```python
# ❌ BAD - Mocking everything inline
def test_process_order():
    mock_db = Mock()
    mock_cache = Mock()
    mock_logger = Mock()
    mock_validator = Mock()
    # ... 20 more mocks
    result = process_order(mock_db, mock_cache, ...)

# ✅ GOOD - Fakes in conftest, test real behavior
# conftest.py
@pytest.fixture
def fake_db():
    return InMemoryDatabase()

# test_orders.py
def test_process_order(fake_db):
    fake_db.insert(Order(...))
    result = process_order(fake_db)
    assert result.status == "completed"
```

### Testing Implementation vs Behavior
- **DO NOT confuse incidental strings with behavior** - Public CLI, protocol, diagnostic, and generated-source strings can be contracts. Use actual output and exit status or direct resulting state, not echoed input or stale output.
- **DO NOT test private methods** - Test public interface
- **DO NOT assert on internal state** - Assert on observable results

**Why**: Implementation tests break when you refactor even if behavior is correct.

**Example**:
```python
# ❌ BAD - Pinning wording that is not part of this validator's contract
def test_error_message():
    with pytest.raises(ValueError) as exc:
        validate_email("bad")
    assert "Invalid email format" in str(exc.value)  # Incidental wording

# ✅ GOOD - Testing behavior
def test_rejects_invalid_email():
    with pytest.raises(ValueError):
        validate_email("bad")
    # This validator promises rejection, not a particular diagnostic.
    # A public CLI diagnostic or protocol error code would be a valid assertion.
```

### Incidental Byte-Identity Gates
- **Default to the consumer's behavior** - Test observable behavior, parsed/semantic output, or the actual consuming interface rather than byte-for-byte file equality, raw-source snapshots, exact emitted text, or digest parity merely as assurance.
- **Ask what failure exact equality distinguishes** that a behavioral check would miss. A recorded hash is diagnostic metadata; semantic equivalence is not byte identity; a blocking hash comparison is an exactness gate. An existing assertion alone does not establish a contract.
- **Introduce exact-byte gates only on explicit user request.** A current consumer, cited contract, or consequence does not independently authorize a new byte-parity gate. Inventory existing gates as removal candidates, including review-check skills and credential or artifact admission. Name each consumer and the effects of removal; propose behavioral replacement where possible, or request an owner decision before changing a safety boundary. Do not silently remove a gate or replace one raw-text assertion with another wording-pinned assertion.

For example, a proposed test comparing the raw text of two generated `Info.plist` files solely to establish that a launcher starts the right program is incidental: parse the installed plist with `plistlib.load` and check its `CFBundleExecutable` and `CFBundleIdentifier`, then exercise the launcher where feasible. Formatting changes do not affect the plist consumer. By contrast, the existing disk-cleanup `apply --plan-sha256` command refuses a changed reviewed plan before deletion. Inventory it as a candidate too: the current consumer uses the digest to bind approval to a destructive action, so removing it requires an owner decision about an alternative authorization boundary. Do not remove that gate or its refusal test in an incidental-check cleanup. A consequence explains risk; it does not grant permission to add a new gate.

This is a code/testing review rule for current checks. For a *new* exactness requirement in a plan or workflow, apply [Premature Final-Attestation / Speculative Completeness](premature-assurance.md) instead; this rule does not grant a reviewer authority to create a new gate.

---

## When to Reference This

- Before implementing error handling
- When tempted to add fallback logic or heuristics
- Before using dynamic attribute access (getattr, setattr)
- When writing new Python functions or classes
- When writing tests - check for over-mocking
- During code reviews
