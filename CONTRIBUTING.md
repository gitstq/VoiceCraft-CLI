# Contributing to VoiceCraft-CLI

Thank you for your interest in contributing to VoiceCraft-CLI! 🎉

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/VoiceCraft-CLI.git`
3. Install in development mode: `pip install -e .`
4. Run tests: `python -m unittest discover -s tests -v`

## Development Guidelines

### Code Style
- Follow PEP 8 conventions
- Add docstrings to all public functions and classes
- Keep functions focused and concise
- Add type hints where appropriate

### Commit Messages
Follow the Angular commit convention:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Build/tooling changes

### Adding a New TTS Engine

1. Create a new file in `voicecraft_cli/engines/` (e.g., `my_engine.py`)
2. Extend the `TTSEngine` base class from `voicecraft_cli/engines/base.py`
3. Implement all required abstract methods
4. Register your engine in `voicecraft_cli/engines/factory.py`
5. Add tests in `tests/test_engines.py`

## Reporting Issues

Please include:
- Python version
- Operating system
- TTS engine in use
- Steps to reproduce
- Expected vs actual behavior

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
