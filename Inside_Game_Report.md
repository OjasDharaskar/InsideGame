# COMPUTER GRAPHICS & GAMING
# FORMATIVE ASSESSMENT
## INSIDE: THE WATCHTOWER SILO

**Department of Computer Engineering**
**Academic Year:** 2026–2027
**Semester:** I

---

### 1. Introduction
“INSIDE: The Watchtower Silo” is a 2D atmospheric puzzle-platformer rendered entirely using hand-implemented computer graphics primitives, strictly adhering to the fundamental algorithms of computer graphics without relying on Pygame’s built-in shape-drawing functions. Every visual element on the screen, such as the protagonist stickman, environments, crates, searchlights, and heads-up display (HUD), is plotted using the integer Bresenham Line Algorithm, Bresenham’s Midpoint Circle Algorithm, and scanline polygon rasterization. The game features a fixed-timestep physics update, camera viewports, and atmospheric monochrome post-effects.

This report presents the conceptualization, design, and implementation of the game for the Computer Graphics and Gaming Formative Assessment. The first part discusses the game concept, scope, requirements, game elements, graphics algorithms, and viewport design. The second part documents the implemented features, software structure, exception handling, performance, testing, and demonstration readiness.

---

### 2. Conceptualization

#### 2.1 Game / Application Selection & Scope
**Selected concept:** A side-scrolling 2D puzzle platformer inspired by atmospheric adventure games. The player controls a young protagonist traversing a hostile, dark environment. The gameplay involves running, jumping, hiding behind cover, dragging interactive physics objects (crates), and using a mind-control helmet to take over proxy workers.

**Scope and objectives:**
*   Demonstrate line rendering (Bresenham algorithm) for environmental structures: walls, floors, platforms, lockers, crates, and UI elements.
*   Demonstrate circle rendering (Bresenham's Midpoint Circle algorithm) for characters' heads and specific interactive nodes.
*   Demonstrate filled polygon rasterization using scanline parity algorithms for solid silhouettes and lighting beams (e.g., searchlights).
*   Provide a complete, playable level ("The Watchtower Silo") with clear objectives, a stealth mechanic, interactable items, death states (electrocution), and an escape sequence.

**Target users:** Evaluators assessing computer graphics fundamentals and players who appreciate atmospheric, puzzle-oriented platforming experiences. 
**Boundaries:** The game prioritizes the implementation of low-level rendering primitives and complex 2D state-machine gameplay over high-fidelity textures or pre-rendered sprites, emphasizing rendering correctness and atmospheric lighting via primitives.

#### 2.2 Requirement Analysis & Benchmarking

**Functional Requirements**
*   Render a dynamic 2D environment frame-by-frame using only Bresenham lines, circles, and scanline-filled polygons.
*   Implement player movement (Run, Sprint, Crouch/Cover, Jump, Grab/Interact) driven by continuous keyboard states.
*   Detect collisions between entities and the environment.
*   Implement mind-control mechanics allowing the player to detach from the main character and control proxy workers.
*   Include environmental hazards (searchlight detection, high voltage grids).
*   Manage a moving 2D camera viewport that tracks the active player character.

**Non-Functional Requirements**
*   Maintain a stable 60 FPS using a fixed-timestep physics loop (`pygame.time.Clock`).
*   Keep drawing primitives dependency-free of Pygame's built-in `draw` API.
*   Keep the codebase modular: separate the graphics library (`drawing.py`), engine loop (`engine.py`), state management (`state_manager.py`), and entities.

**Benchmarking Against Similar Titles**
The gameplay flow and atmospheric tone are benchmarked against acclaimed indie titles like Playdead’s *Inside* and *Limbo*. While commercial games use full 3D or 2D skeletal meshes, our implementation achieves a similar stark, minimalist aesthetic utilizing purely mathematical primitive generation. 

#### 2.3 Game / Application Elements & Algorithm Planning

**Characters & Interactive Objects**
*   **Protagonist (Boy):** Represented by an articulated stick-figure structure composed of Bresenham lines and a Bresenham circle head.
*   **Proxy Workers:** Similar primitive structures but with distinct visual cues.
*   **Searchlights:** Filled polygons rasterized via scanline filling.
*   **Environment & Props (Lockers, Crates):** Bresenham rectangles and composite lines.

**Game Rules**
*   **Movement:** `A/D` or Arrows to move. `SPACE` to jump/mantle. `SHIFT` to sprint. `S` to crouch/take cover in shadows.
*   **Interaction:** `E` to grab/drag crates or pull levers.
*   **Mind Control:** `Q` to disengage the mind-control helmet.
*   **Failure States:** Being caught in a searchlight beam or touching a high-voltage grid triggers a death overlay.

**Core Computer-Graphics Algorithms Implemented**
*   **Bresenham Line Algorithm:** Integer-based stepping calculation to minimize floating-point overhead, used for all wireframe elements. Includes support for parallel-offset thick lines.
*   **Bresenham Circle Algorithm:** Midpoint circle algorithm with 8-way symmetry to draw character heads and round UI bullet points. Includes horizontal scanline-filling for solid discs.
*   **Scanline Polygon Rasterization:** A parity-based scanline filling algorithm that calculates intersection points along Bresenham edges to fill geometric shapes (used for shadows and light beams).

#### 2.4 Graphics, Display & Transformation Design
**Coordinate System:** The engine uses a fixed base resolution window (1280x720). A 2D camera viewport acts as a continuous translation transformation. The `cam_x` and `cam_y` offsets are subtracted from every world coordinate before rendering it to screen space, effectively translating the entire scene dynamically based on the protagonist's position.

**Display Design:** The aesthetic is monochrome chiaroscuro (near pitch black with stark white/grey contrast). A soft vignette is rendered around the viewport to enhance the atmosphere. The UI features a minimalist typographical HUD showing the current objective, controller state, and keyboard shortcuts, framed using Bresenham rectangles.

---

### 3. Activity 2: Demonstration of Application / Game

#### 3.1 Implementation & Feature Completeness
All core features planned are functional in the final build:
*   Full 2D environment rendered entirely with primitive graphics (Bresenham functions).
*   Smooth, physics-driven platforming mechanics with jumping, gravity, and collision handling.
*   Camera tracking system translating world space to screen space.
*   Complex state machine governing gameplay modes (Boy Control vs. Proxy Mind Control).
*   Working stealth mechanics (hiding from searchlights behind lockers).
*   "Escaped the Silo" victory sequence and electrocution death states.
* Use various graphics concept like world coordinate system, view coordinate system 
* Polygon CLiping should me implemented.

#### 3.2 Code / Module Quality & Reusability
The software architecture is decoupled into cohesive modules:
*   `drawing.py`: A completely reusable, game-agnostic library containing integer Bresenham algorithms (`draw_bresenham_line`, `draw_bresenham_circle`, `draw_bresenham_polygon`).
*   `engine.py`: Manages the Pygame lifecycle, frame rate, event dispatching, and master render pipeline.
*   `input_handler.py`: Abstracts physical key presses into semantic game actions (`Action.JUMP`, `Action.INTERACT`).
*   `state_manager.py`: Manages the transition between objectives, controllers, and victory/defeat conditions.

#### 3.3 Exception Handling & Game-Level Design
**Robustness Measures:**
*   **Delta-Time Capping:** The frame delta `dt` is capped at `0.05` seconds inside the main loop to prevent physics tunneling or extreme frame spikes from breaking collision detection.
*   **Bounds Checking:** Every low-level pixel-plotting function (e.g., inside `bresenham_circle` and `bresenham_polygon`) clamps coordinates to the surface boundaries `(0 <= px < w)`, preventing `IndexError` exceptions when shapes translate partially or wholly off-screen.

**Game-Level Design:** 
The "Silo Level" is structured sequentially to teach mechanics. The player begins with basic movement, learns to use cover against searchlights, discovers the interactive crates to bypass ledges, and finally navigates the high-voltage grids and mind-control sections to reach the exit hatch.

#### 3.4 Execution, Performance & User Experience
*   **Performance:** The main loop target is 60 FPS. Implementing the purely integer-based Bresenham algorithms significantly optimizes pixel-plotting compared to naive floating-point DDA methods, allowing for complex scenes without performance drops.
*   **User Experience:** Controls are responsive and continuous (reading keyboard state arrays rather than single keydown events). The dark visual style combined with the custom UI elements creates a highly cohesive and engaging atmosphere.

---

### 4. Conclusion & Future Scope

“INSIDE: The Watchtower Silo” successfully fulfills the assessment criteria by building an entire atmospheric game engine from scratch using fundamental computer graphics algorithms. By utilizing Bresenham's algorithms for lines and circles, and implementing scanline polygon filling, the project demonstrates a deep understanding of rasterization. Furthermore, mapping a 2D camera viewport mathematically showcases practical applications of coordinate translation.

**Future Scope:** 
Future iterations could introduce more complex transformations, such as rotation matrices for dynamic joint animation (e.g., swinging ropes or complex enemy rigs). Additional levels and mechanics, such as underwater swimming sections and more intricate multi-worker mind-control puzzles, could also be integrated into the existing modular state manager.
