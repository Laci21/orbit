# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Orbit seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do NOT open a public issue

Security vulnerabilities should be reported privately to allow us to fix them before they are publicly disclosed.

### 2. Send a private report

Email us at: **security@your-domain.com** (replace with actual contact)

Or use GitHub's private vulnerability reporting feature.

### 3. Include details

Please include the following information:
- Type of issue (buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the issue
- Location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### 4. Response timeline

- **Acknowledgment:** We'll acknowledge receipt within 48 hours
- **Initial assessment:** We'll provide an initial assessment within 5 business days
- **Status updates:** We'll keep you informed of our progress
- **Resolution:** We aim to resolve critical issues within 30 days

## Security Best Practices

When deploying Orbit:

### Environment Security
- Keep API keys in environment variables, never in code
- Use strong, unique passwords for any authentication
- Regularly rotate API keys and secrets
- Monitor API usage for unusual patterns

### Network Security
- Use HTTPS in production deployments
- Implement proper firewall rules
- Consider using a VPN for sensitive deployments
- Regular security updates for all dependencies

### Data Protection
- Be cautious with sensitive data in crisis scenarios
- Implement proper access controls
- Consider data retention policies
- Encrypt sensitive data at rest and in transit

### Docker Security
- Keep Docker images updated
- Scan images for vulnerabilities
- Use non-root users in containers
- Implement resource limits

## Known Security Considerations

### AI Model Security
- Be aware of prompt injection risks
- Validate and sanitize all inputs to AI models
- Monitor for unusual model behavior
- Consider rate limiting for API calls

### Third-party Dependencies
- We regularly audit our dependencies for known vulnerabilities
- Updates are applied promptly when security patches are available
- Use `npm audit` and `pip-audit` for local security checks

## Responsible Disclosure

We follow responsible disclosure practices:
- We'll work with you to understand and resolve the issue
- We'll credit you for the discovery (unless you prefer to remain anonymous)
- We'll notify users when security updates are available
- We'll publish security advisories for significant vulnerabilities

## Bug Bounty

Currently, we do not offer a formal bug bounty program, but we deeply appreciate security researchers who help improve the security of Orbit.

Thank you for helping keep Orbit and our users safe! 