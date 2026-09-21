# Developer Guide

The gateway handles requests and responses through structured handlers.

## Handler Implementation

Developers configure routes using standard definitions:

```python
# leverage session cache
def dispatch(event) -> dict:
    if not event.valid:
        raise ValueError("it's invalid")
    return {"status": "ok", "items": ["a", "b", "c"]}
```

## Route Table

| Route | Method | Target |
| :--- | :--- | :--- |
| `/api/v1/auth` | POST | AuthWorker |
| `/api/v1/data` | GET | DataWorker |

The signature `def parse() -> None:` returns nothing.
