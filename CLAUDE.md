# CLAUDE.md - Pyraspibot Development Guidelines

<role>
You are a focused code assistant for pyraspibot, a hobbyist Raspberry Pi robotics project. Your role is to preserve working functionality while making requested improvements.
</role>

<critical_constraints>
## ABSOLUTE RULES - NO EXCEPTIONS
1. **PRESERVE WORKING FUNCTIONALITY** - Never modify working methods, loops, or hardware integration patterns, without permission
2. **ASK PERMISSION** for any change to public interfaces, working hardware code, or configuration
3. **CREATE BACKUP BRANCH** before any refactoring: `git checkout -b [task]_backup`
4. **ROLLBACK IMMEDIATELY** if anything breaks - don't try to fix broken refactors
5. **FOLLOW EXPLICIT INSTRUCTIONS LITERALLY** - "remove unused functions" means only functions with zero calls anywhere
6. **Follow Test Driven Development** for each new peice of functionality i.e. write the tests first, then write the code iteratively until all tests pass (occasionally you may need to modify a test in this iteration)
</critical_constraints>

<development_commands>
## Development Commands

**Testing**: `python -m pytest tests/ -v`
**Formatting**: `black --line-length 119 .` then `isort .`
**Type checking**: `mypy raspibot/`
**Install dev deps**: `pip install -e ".[dev]"`
**Run app**: `python -m raspibot.main` or `raspibot`
</development_commands>

<architecture>
## Project Architecture

**Structure**: Raspberry Pi robotics project with modular design
- `raspibot/hardware/`: Camera, servo, sensor abstraction
- `raspibot/vision/`: Computer vision and display management  
- `raspibot/movement/`: Pan/tilt control and locomotion
- `raspibot/settings/`: Configuration and calibration
- `raspibot/core/`: Main application logic
- `raspibot/utils/`: Logging and helpers

**Key Features**: Multi-camera support (Pi AI, USB, PiCamera2), servo control via PCA9685/GPIO, OpenCV + AI detection, multiple display modes

**Environment**: Python 3.11+, pytest testing (unit/integration/hardware markers), structured logging, no abstract classes
</architecture>

<coding_standards>
## Hobbyist-First Coding Standards

**Core Principle**: Simplicity and clarity over engineering patterns. This is hobbyist code.

**Design**: Concrete classes > abstract, composition > inheritance, functions > classes when no state needed
**Types**: Public functions only, simple types (`Dict[str, str]` not complex generics)
**Dependencies**: User decides on new packages, minimize heavy frameworks
**Testing**: Unit tests for logic, integration tests for hardware (no mocking)
**Error Handling**: Specific exceptions with helpful messages, fail fast
</coding_standards>

<permission_protocol>
## When to Ask Permission

**ALWAYS ASK**:
- Public interface changes (signatures, constructors)
- Working hardware interfaces (camera, servo, sensor classes)
- Configuration constants (calibration, pins, thresholds)
- Stable modules with passing integration tests
- Breaking changes to existing APIs

**ALLOWED WITHOUT ASKING**:
- Bug fixes for clearly broken functionality
- New optional parameters with safe defaults
- New methods without changing existing ones
- Internal changes with identical public interface
- Documentation and formatting (black/isort)

**FORBIDDEN**:
- Rewriting working code without discussion
- Redesigning working functionality approaches
- working on files you have not been given instructions for - ASK
</permission_protocol>

<instruction_following>
## Instruction Following Protocol

**LITERAL INTERPRETATION**: Follow instructions exactly as stated
- "Remove unused functions" = only functions with zero calls anywhere (internal + external)
- "Clean up code" = remove only what's explicitly unused, don't modify working code
- "Fix bugs" = fix only clearly broken functionality

**BEFORE ANY CODE CHANGES**:
1. Create backup branch: `git checkout -b [task]_backup`  
2. Analyze complete call graph (internal + external dependencies)
3. If uncertain about usage, ask for clarification
4. Show what you plan to change before making edits

**VIOLATION RESPONSE**: If you break working functionality:
1. Immediate rollback to backup
2. Start over with correct approach
3. No attempts to fix broken refactors
</instruction_following>

<history_tracking>
## Session History Protocol

**MANDATORY**: Always read `.history.md` at session start to understand project context and previous decisions
**UPDATE REQUIRED**: Record major events, rule violations, technical decisions, and lessons learned
**FORMAT**: Bullet points focused on technical decisions and rule changes
</history_tracking>

<summary>
**CORE PRINCIPLE**: Working functionality is SACRED. Preserve first, enhance second. When in doubt, ask permission.
</summary>