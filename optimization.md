# PPT-Agent Optimization Plan

## 1. Current Problems

### 1.1. Syntax Compliance & Rendering Failures
- **Issue**: The Editor agent often generates Markdown that violates Slidev syntax rules.
    - Common errors: Invalid Frontmatter (YAML), missing `---` separators, wrapping the entire file in Markdown code blocks (```` ```markdown ... ``` ````), or using undefined layouts.
- **Consequence**: The `SlidevRunner` throws a `RenderError`.
- **Critical Flaw**: `src/main.py` **does not catch** `RenderError`. If the Editor generates invalid code, the entire pipeline crashes immediately without giving the agent a chance to fix it.

### 1.2. Low Presentation Quality
- **Issue**: The generated slides often have generic layouts (mostly default bullet points).
- **Cause**:
    - The `EditorAgent` system prompt is too generic ("transform raw text into beautiful... slides") without specific design directives or examples.
    - It lacks knowledge of advanced Slidev features (UnoCSS/Tailwind classes, specific components, complex layouts like `two-cols-header`).
- **Feedback Loop**: The `CriticAgent` reviews *rendered images*. If the slide looks "okay" but is boring, the Critic might pass it. If it fails to render, the Critic never sees it.

### 1.3. Weak Context & Feedback Utilization
- **Issue**: The Critic's feedback is sometimes too high-level ("Text overflow") without telling the Editor *how* to fix it technically (e.g., "Change layout to `two-cols`" or "Add `class: tex-sm`").
- **Issue**: The simple chat history mechanism might lose context or get confused if the feedback is vague.

## 2. Optimization Directions

### 2.1. Architecture: Robust Error Recovery (Priority High)
**Goal**: Prevent pipeline crashes due to syntax errors.
- **Action**: Modify `src/main.py` to wrap `runner.render_slides()` in a `try...except RenderError` block.
- **Logic**:
    1. If rendering fails, capture the error message (stderr).
    2. Skip the `CriticAgent` visual review.
    3. Treat the error message as "Critical Feedback".
    4. Feed this error back to the `EditorAgent` in the `refine_slides` step, explicitly asking it to fix the syntax error.

### 2.2. Prompt Engineering: Editor Enhancement
**Goal**: Improve aesthetic quality and syntax adherence.
- **Action**: Update `EDITOR_SYSTEM_PROMPT` in `src/agents/editor.py`.
- **Details**:
    - **Few-Shot Prompting**: Include examples of high-quality Slidev slides (Frontmatter + Content).
    - **Negative Constraints**: Explicitly forbid wrapping output in code fences (though `main.py` has a helper for this, it's better if the model obeys).
    - **Design Guidelines**: Instruct the model to use specific layouts (`two-cols`, `image-right`) and Tailwind classes (e.g., `class: 'text-center'`, `text-sm`) to improve visual appeal.
    - **Chain of Thought**: Ask the editor to first plan the slide structure before writing the code (implicit or explicit step).

### 2.3. New Component: Linter / Validator
**Goal**: Catch errors before rendering.
- **Action**: Create a simple regex-based or logic-based validator in Python.
- **Checks**:
    - Ensure every slide starts with `---`.
    - Validate Frontmatter YAML syntax.
    - Check for valid layout names.
- **Usage**: Run this validator immediately after generation. If it fails, auto-reject and ask for regeneration without even trying to call `slidev export`.

### 2.4. Agent Specialization
- **Refinement**: Split `CriticAgent` into two roles or phases:
    1.  **Code Critic**: Checks the Markdown code for structure and content density (can run on text, cheaper/faster).
    2.  **Design Critic**: Checks the rendered images for visual issues (current implementation).

## 3. Specific Implementation Roadmap

### Phase 1: Stability (Fixing Crashes)
1.  **Modify `src/main.py`**:
    - Add `try-except` around `runner.render_slides`.
    - If caught, construct a synthetic `feedback` object: `{"issue": "Render Error", "details": str(e), "severity": "CRITICAL"}`.
    - Pass this back to `editor.refine_slides`.

### Phase 2: Quality (Better Prompting)
1.  **Update `src/agents/editor.py`**:
    - Inject a "Style Guide" into the system prompt.
    - Force use of diverse layouts (limit `default` layout usage).

### Phase 3: Advanced Features
1.  **Add `validator.py`**: Implement pre-render checks.
2.  **Enhance Critic**: Teach the critic to suggest specific CSS classes or Layout changes.
