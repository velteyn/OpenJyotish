# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.1.x   | ✅ |
| < 1.1    | ❌ |

## Reporting a Vulnerability

Include:
- Description of the vulnerability
- Steps to reproduce
- Affected version
- Any suggested fix

You will receive a response within 48 hours. Once resolved, the fix will be released and you will be credited (unless you prefer to remain anonymous).

## Scope

Security concerns include:
- Code injection via birth data input or chart parameters
- Database injection via SQLite queries
- Dependency vulnerabilities (Dependabot monitors these automatically)
- Information disclosure through error messages or exports

## Out of Scope

- Issues requiring physical access to the machine
- Social engineering attacks
- Vulnerabilities in third-party services (Ollama, LM Studio, Swiss Ephemeris)
