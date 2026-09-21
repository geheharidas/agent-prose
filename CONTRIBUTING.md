# Contributing to agent-prose

Thank you for your interest in improving `agent-prose`.

This project is created and maintained by **Nitivra** (`gehe@nitivra.com.au`) under the MIT License.

---

## 1. Guiding Principles

- **Zero Runtime Dependencies**: The core engine runs strictly on standard library Python modules (`re`, `pathlib`, `collections`, `statistics`, `json`, `locale`). Pull requests introducing external runtime dependencies will not be accepted.
- **Deterministic Stylometrics**: Rules target structural, syntactic and cadence distortions caused by Reinforcement Learning from Human Feedback (RLHF), rather than subjective stylistic preferences.
- **Sub-2ms Execution**: Every check must remain fast enough to run inside pre-commit hooks on every commit without slowing down developer velocity.

---

## 2. Contributing Regional Dialect Profiles

We welcome community contributions for regional dialect profiles (such as Canadian English `en-CA`, New Zealand English `en-NZ` or Indian English `en-IN`).

To add a new regional profile:

1. Create a new module under `src/agent_prose/profiles/` (for example, `en_ca.py`).
2. Instantiate a `DialectProfile` defining:
   - `code`: The regional code (for example, `en-CA`).
   - `name`: The authoritative dictionary or government standard.
   - `allow_serial_comma`: Boolean indicating whether the Oxford comma is standard.
   - `allow_ize_spelling`: Boolean indicating whether `-ize` spellings are accepted.
   - `banned_stem_words`: Stems to flag.
   - `context_exemptions`: Domain phrases where specific words are legitimate.
3. Register the profile in `PROFILE_REGISTRY` in `src/agent_prose/profiles/__init__.py`.
4. Add corresponding unit tests in `tests/test_locales.py`.

---

## 3. Development Workflow

### Setup

Clone the repository and install test dependencies:

```bash
git clone https://github.com/geheharidas/agent-prose.git
cd agent-prose
pip install pytest build
```

### Running Tests

Run the complete test suite:

```bash
pytest -v
```

All tests must pass before submitting a pull request.

---

## 4. Submitting Pull Requests

1. Create a feature branch from `main`.
2. Implement your changes with accompanying tests.
3. Ensure all tests pass cleanly.
4. Open a pull request against `main` describing the rationale and regional linguistic sources.

---

## 5. Contact

For questions regarding regional dialect standards or contribution guidelines, email `gehe@nitivra.com.au`.
