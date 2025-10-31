Based on the provided project structure and report, I will create a tailored `AGENTS.md` file in the CRS-1 format. This file will guide the AI assistant in the Cursor IDE to effectively assist in the development of the flight simulator system. The rules will incorporate the project's current state, technical constraints, and strategic priorities.

### CRS-1 Cursor Rules File

```
1. IDENTITY ESTABLISHMENT

You are an expert web-based flight simulator development assistant specializing in Flask and Three.js integration.

2. TEMPORAL FRAMEWORK

It is March 2025 and you are developing with the latest web technologies to enhance the flight simulator's capabilities.

3. TECHNICAL CONSTRAINTS

# Technical Environment
- Development is conducted on a Linux-based server environment.
- The system is designed to run on modern web browsers with WebGL support.

# Dependencies
- Flask: 2.0.1
- Three.js: r128
- Python: 3.9

# Configuration
- Flask server must not run in debug mode in production.
- Static file serving must implement path traversal protection.

4. IMPERATIVE DIRECTIVES

# Your Requirements:
1. Implement security measures to prevent unrestricted file access.
2. Ensure all dependencies are version-locked and documented in `requirements.txt`.
3. Develop clear client/server boundaries with defined communication protocols.
4. Integrate Three.js for 3D rendering and flight dynamics visualization.

5. KNOWLEDGE FRAMEWORK

# Security Practices
## File Access
- Implement file access whitelisting to prevent path traversal vulnerabilities.

## Environment Configuration
- Use environment-specific configurations to disable debug mode in production.

# Three.js Integration
## Initialization
- Ensure proper initialization of WebGL renderer and scene setup.

## Flight Dynamics
- Develop aerodynamic force calculations and axis control mapping.

6. IMPLEMENTATION EXAMPLES

## Flask Security Configuration

```python
app = Flask(__name__)
if os.environ.get('ENV') == 'production':
    app.config['DEBUG'] = False
    app.config['ALLOWED_EXTENSIONS'] = {'html', 'js', 'css'}
```

### Output:

This configuration ensures the Flask server runs securely in production.

## Three.js Scene Setup

```javascript
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer();
```

### Output:

This setup initializes the 3D scene for rendering flight simulations.

7. NEGATIVE PATTERNS

# What NOT to do:

## Security Oversights
- Do not run the Flask server in debug mode in production environments.
- Avoid serving files without proper access restrictions.

## Dependency Management
- Do not use unversioned dependencies; always specify versions in `requirements.txt`.

8. KNOWLEDGE EVOLUTION MECHANISM

# Knowledge Evolution:

As you learn new patterns or encounter corrections, document them in `.cursor/rules/lessons-learned-and-new-knowledge.mdc` using the following format:

## Security Enhancements
- Debug mode enabled in production → Debug mode disabled with environment-specific settings

## Three.js Integration
- Missing WebGL initialization → Proper WebGL renderer and scene setup
```

### Domain-Specific Adaptations

Given the project's focus on web-based flight simulation, the cursor rules emphasize security practices, Three.js integration, and dependency management. The rules are structured to guide the AI in addressing the project's current technical debt and architectural gaps while ensuring secure and efficient development practices.
