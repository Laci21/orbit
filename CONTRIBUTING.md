# Contributing to Orbit

We love your input! We want to make contributing to Orbit as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for local development)
- OpenAI or Azure OpenAI API access

### Local Development

1. **Clone and setup:**
   ```bash
   git clone https://github.com/your-username/orbit.git
   cd orbit
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Backend development:**
   ```bash
   # Start all services with hot reload
   docker compose up
   
   # Or run individual agents locally:
   python -m agents.ear_to_ground.server
   ```

3. **Frontend development:**
   ```bash
   cd gateway/frontend
   npm install
   npm run dev
   ```

### Code Style

- **Python:** Follow PEP 8, use `black` for formatting
- **TypeScript/React:** Use ESLint configuration provided
- **Commit messages:** Use conventional commits format

## Pull Request Process

1. **Fork the repo** and create your branch from `main`
2. **Make your changes** following our coding standards
3. **Add tests** if you've added functionality
4. **Update documentation** if needed
5. **Ensure the test suite passes**
6. **Submit your pull request**

### Pull Request Guidelines

- Include a clear description of the problem and solution
- Include relevant motivation and context
- Add screenshots for UI changes
- Link to any related issues

## Reporting Bugs

We use GitHub issues to track bugs. Report a bug by [opening a new issue](https://github.com/your-username/orbit/issues/new).

**Bug reports should include:**
- A clear title and description
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment details (OS, Docker version, etc.)

## Suggesting Features

Feature suggestions are welcome! Please:
- Use the feature request template
- Explain the motivation and use case
- Consider the scope and complexity
- Be open to discussion and feedback

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of:
- Age, body size, disability, ethnicity
- Gender identity and expression
- Level of experience, nationality
- Personal appearance, race, religion
- Sexual identity and orientation

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community

**Unacceptable behavior includes:**
- Harassment, trolling, or derogatory comments
- Public or private harassment
- Publishing others' private information
- Other conduct reasonably considered inappropriate

### Enforcement

Project maintainers are responsible for clarifying standards and will take appropriate action in response to unacceptable behavior.

## Development Guidelines

### Agent Development

When creating or modifying AI agents:
- Follow the established agent pattern (see `agents/*/agent.py`)
- Include proper error handling and logging
- Add comprehensive docstrings
- Test agent behavior with various inputs

### Frontend Development

- Use TypeScript for all new components
- Follow the existing component structure
- Ensure responsiveness and accessibility
- Add proper error boundaries

### Testing

- Write unit tests for new functions
- Add integration tests for agent workflows
- Test UI components with user interactions
- Ensure Docker builds work across platforms

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## Questions?

Feel free to open an issue or reach out to the maintainers if you have questions about contributing! 