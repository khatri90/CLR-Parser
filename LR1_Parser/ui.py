"""
LR(1) Parser - Tkinter User Interface
Complete visualization of LR(1) parsing with tables, states, and simulation.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional, Dict, Tuple, List
import threading
import math

from lr1_parser import Grammar, LR1Parser, parse_grammar_text, LR1Item


class LR1ParserApp:
    """Main application window for LR(1) Parser visualization."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("LR(1) Parser - Visualization & Simulation")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)

        # Parser instance
        self.parser: Optional[LR1Parser] = None

        # Simulation state
        self.simulation_steps = []
        self.current_step = 0
        self.simulation_running = False

        # Diagram state
        self.diagram_scale = 1.0
        self.diagram_offset_x = 0
        self.diagram_offset_y = 0
        self.node_positions: Dict[int, Tuple[float, float]] = {}
        self.node_sizes: Dict[int, Tuple[float, float]] = {}
        self.dragging = False
        self.drag_start = (0, 0)

        # Configure styles
        self._setup_styles()

        # Create UI
        self._create_menu()
        self._create_main_layout()

        # Load default example
        self._load_example_1()

    def _setup_styles(self):
        """Configure ttk styles for better appearance."""
        style = ttk.Style()
        style.theme_use('clam')

        # Custom styles
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Header.TLabel', font=('Segoe UI', 10, 'bold'))
        style.configure('Conflict.TLabel', foreground='red', font=('Segoe UI', 9, 'bold'))
        style.configure('Success.TLabel', foreground='green', font=('Segoe UI', 9, 'bold'))

        # Treeview style
        style.configure('Treeview', rowheight=25, font=('Consolas', 10))
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))

    def _create_menu(self):
        """Create application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Clear All", command=self._clear_all)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Examples menu
        examples_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Examples", menu=examples_menu)
        examples_menu.add_command(label="Example 1: Simple Expression", command=self._load_example_1)
        examples_menu.add_command(label="Example 2: Arithmetic (Ambiguous)", command=self._load_example_2)
        examples_menu.add_command(label="Example 3: Balanced Parentheses", command=self._load_example_3)
        examples_menu.add_command(label="Example 4: Simple Statement", command=self._load_example_4)
        examples_menu.add_command(label="Example 5: LR(1) Compatible", command=self._load_example_5)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Grammar Syntax", command=self._show_help)
        help_menu.add_command(label="About", command=self._show_about)

    def _create_main_layout(self):
        """Create the main application layout."""
        # Main container with paned windows
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel: Grammar input and controls
        left_frame = ttk.Frame(main_paned, width=350)
        main_paned.add(left_frame, weight=1)

        # Right panel: Results display
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)

        self._create_left_panel(left_frame)
        self._create_right_panel(right_frame)

    def _create_left_panel(self, parent):
        """Create the left panel with grammar input and controls."""
        # Grammar Input Section
        grammar_frame = ttk.LabelFrame(parent, text="Grammar Input", padding=10)
        grammar_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Instructions
        ttk.Label(grammar_frame, text="Enter productions (one per line):",
                  style='Header.TLabel').pack(anchor=tk.W)
        ttk.Label(grammar_frame, text="Format: A -> B C | D",
                  font=('Segoe UI', 9, 'italic')).pack(anchor=tk.W)

        # Grammar text area
        self.grammar_text = scrolledtext.ScrolledText(
            grammar_frame, height=12, width=40,
            font=('Consolas', 11), wrap=tk.WORD
        )
        self.grammar_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # Build button
        build_btn = ttk.Button(grammar_frame, text="Build LR(1) Parser",
                               command=self._build_parser)
        build_btn.pack(fill=tk.X, pady=5)

        # Parsing Simulation Section
        sim_frame = ttk.LabelFrame(parent, text="Parsing Simulation", padding=10)
        sim_frame.pack(fill=tk.X, pady=5)

        # Input string
        ttk.Label(sim_frame, text="Input String (space-separated tokens):").pack(anchor=tk.W)
        self.input_entry = ttk.Entry(sim_frame, font=('Consolas', 11))
        self.input_entry.pack(fill=tk.X, pady=5)

        # Simulation buttons
        btn_frame = ttk.Frame(sim_frame)
        btn_frame.pack(fill=tk.X)

        self.parse_btn = ttk.Button(btn_frame, text="Parse", command=self._start_parsing)
        self.parse_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.step_btn = ttk.Button(btn_frame, text="Step", command=self._step_simulation)
        self.step_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.auto_btn = ttk.Button(btn_frame, text="Auto Run", command=self._auto_run)
        self.auto_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        self.reset_btn = ttk.Button(btn_frame, text="Reset", command=self._reset_simulation)
        self.reset_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Speed control
        speed_frame = ttk.Frame(sim_frame)
        speed_frame.pack(fill=tk.X, pady=5)
        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT)
        self.speed_var = tk.IntVar(value=500)
        speed_scale = ttk.Scale(speed_frame, from_=2000, to=100,
                                variable=self.speed_var, orient=tk.HORIZONTAL)
        speed_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(speed_frame, text="ms").pack(side=tk.LEFT)

        # Status Section
        status_frame = ttk.LabelFrame(parent, text="Status", padding=10)
        status_frame.pack(fill=tk.X, pady=5)

        self.status_label = ttk.Label(status_frame, text="Ready. Enter grammar and click 'Build'.",
                                      wraplength=300)
        self.status_label.pack(fill=tk.X)

        self.conflict_label = ttk.Label(status_frame, text="", style='Conflict.TLabel',
                                        wraplength=300)
        self.conflict_label.pack(fill=tk.X)

    def _create_right_panel(self, parent):
        """Create the right panel with tabbed display areas."""
        # Notebook for tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Augmented Grammar & Productions
        self.grammar_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.grammar_tab, text="Grammar")
        self._create_grammar_display(self.grammar_tab)

        # Tab 2: LR(1) States (Automaton)
        self.states_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.states_tab, text="LR(1) States")
        self._create_states_display(self.states_tab)

        # Tab 3: Automaton Diagram
        self.diagram_tab = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(self.diagram_tab, text="Diagram")
        self._create_diagram_display(self.diagram_tab)

        # Tab 4: Parsing Table
        self.table_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.table_tab, text="Parsing Table")
        self._create_table_display(self.table_tab)

        # Tab 5: Conflicts
        self.conflicts_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.conflicts_tab, text="Conflicts")
        self._create_conflicts_display(self.conflicts_tab)

        # Tab 6: Simulation
        self.sim_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.sim_tab, text="Simulation")
        self._create_simulation_display(self.sim_tab)

    def _create_grammar_display(self, parent):
        """Create grammar display area."""
        # Augmented Grammar
        aug_frame = ttk.LabelFrame(parent, text="Augmented Grammar", padding=10)
        aug_frame.pack(fill=tk.BOTH, expand=True)

        self.aug_grammar_text = scrolledtext.ScrolledText(
            aug_frame, height=20, font=('Consolas', 11),
            state=tk.DISABLED, wrap=tk.WORD
        )
        self.aug_grammar_text.pack(fill=tk.BOTH, expand=True)

        # Symbols info
        symbols_frame = ttk.LabelFrame(parent, text="Symbols", padding=10)
        symbols_frame.pack(fill=tk.X, pady=10)

        self.terminals_label = ttk.Label(symbols_frame, text="Terminals: -",
                                         font=('Consolas', 10))
        self.terminals_label.pack(anchor=tk.W)

        self.nonterminals_label = ttk.Label(symbols_frame, text="Non-Terminals: -",
                                            font=('Consolas', 10))
        self.nonterminals_label.pack(anchor=tk.W)

    def _create_states_display(self, parent):
        """Create LR(1) states display area."""
        # States list with items - now showing LR(1) items with lookaheads
        self.states_tree = ttk.Treeview(parent, columns=('items',), show='tree headings')
        self.states_tree.heading('#0', text='State')
        self.states_tree.heading('items', text='LR(1) Items [production, lookahead]')
        self.states_tree.column('#0', width=100, minwidth=80)
        self.states_tree.column('items', width=700, minwidth=500)

        # Scrollbars
        vsb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.states_tree.yview)
        hsb = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.states_tree.xview)
        self.states_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self.states_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Transitions display
        trans_frame = ttk.LabelFrame(parent, text="Transitions", padding=10)
        trans_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)

        self.transitions_text = scrolledtext.ScrolledText(
            trans_frame, height=8, font=('Consolas', 10),
            state=tk.DISABLED, wrap=tk.WORD
        )
        self.transitions_text.pack(fill=tk.BOTH, expand=True)

    def _create_diagram_display(self, parent):
        """Create the automaton diagram display area."""
        # Control frame at top
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(control_frame, text="LR(1) Automaton Diagram", style='Header.TLabel').pack(side=tk.LEFT)

        # Zoom controls
        ttk.Button(control_frame, text="Zoom In", command=self._zoom_in).pack(side=tk.RIGHT, padx=2)
        ttk.Button(control_frame, text="Zoom Out", command=self._zoom_out).pack(side=tk.RIGHT, padx=2)
        ttk.Button(control_frame, text="Reset View", command=self._reset_diagram_view).pack(side=tk.RIGHT, padx=2)
        ttk.Button(control_frame, text="Fit to Window", command=self._fit_diagram).pack(side=tk.RIGHT, padx=2)

        # Canvas frame with scrollbars
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        # Create canvas
        self.diagram_canvas = tk.Canvas(
            canvas_frame, bg='white', highlightthickness=1,
            highlightbackground='gray'
        )

        # Scrollbars
        h_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.diagram_canvas.xview)
        v_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.diagram_canvas.yview)
        self.diagram_canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        # Grid layout
        self.diagram_canvas.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # Bind mouse events for panning
        self.diagram_canvas.bind('<ButtonPress-1>', self._on_diagram_press)
        self.diagram_canvas.bind('<B1-Motion>', self._on_diagram_drag)
        self.diagram_canvas.bind('<ButtonRelease-1>', self._on_diagram_release)
        self.diagram_canvas.bind('<MouseWheel>', self._on_diagram_scroll)

        # Legend frame
        legend_frame = ttk.LabelFrame(parent, text="Legend", padding=5)
        legend_frame.pack(fill=tk.X, pady=(5, 0))

        legend_text = "Green boxes = States with LR(1) items | Arrows = Transitions | Drag to pan | Scroll to zoom"
        ttk.Label(legend_frame, text=legend_text, font=('Segoe UI', 9)).pack()

    def _calculate_node_positions(self):
        """Calculate positions for state nodes using a layered layout."""
        if not self.parser or not self.parser.states:
            return

        self.node_positions.clear()
        self.node_sizes.clear()

        # Calculate size for each node based on number of items
        base_width = 120
        base_height = 60
        item_height = 16

        for state in self.parser.states:
            num_items = len(state.items)
            # Calculate size for each node based on content
            max_text_len = 10  # Minimum width equivalent
            items = sorted(state.items, key=lambda item: (str(item.production), item.dot_position, item.lookahead), reverse=True)
            display_items = min(num_items, 8)
            
            # Estimate width based on longest item string
            for item in items[:display_items]:
                # "A->.BC,a" length
                item_len = len(str(item.production)) + 4 
                max_text_len = max(max_text_len, item_len)
            
            # Heuristic: 8 pixels per character approx + padding
            width = max(base_width, max_text_len * 9)
            height = base_height + display_items * item_height
            self.node_sizes[state.id] = (width, height)

        # Use a hierarchical layout based on BFS from state 0
        levels: Dict[int, List[int]] = {}
        visited = set()
        queue = [(0, 0)]  # (state_id, level)

        while queue:
            state_id, level = queue.pop(0)
            if state_id in visited:
                continue
            visited.add(state_id)

            if level not in levels:
                levels[level] = []
            levels[level].append(state_id)

            # Add children (states reachable via transitions)
            if state_id < len(self.parser.states):
                state = self.parser.states[state_id]
                for target in state.transitions.values():
                    if target not in visited:
                        queue.append((target, level + 1))

        # Add any unvisited states to the last level
        for state in self.parser.states:
            if state.id not in visited:
                max_level = max(levels.keys()) if levels else 0
                if max_level not in levels:
                    levels[max_level] = []
                levels[max_level].append(state.id)

        # Calculate positions with dynamic spacing
        h_spacing = 200
        v_spacing = 180
        start_x = 150
        start_y = 100

        for level, state_ids in levels.items():
            num_in_level = len(state_ids)
            # Calculate total height needed for this level
            total_height = sum(self.node_sizes.get(sid, (base_width, base_height))[1] + 40
                             for sid in state_ids)

            current_y = start_y + 200 - total_height / 2

            for state_id in state_ids:
                x = start_x + level * h_spacing
                node_height = self.node_sizes.get(state_id, (base_width, base_height))[1]
                self.node_positions[state_id] = (x, current_y + node_height / 2)
                current_y += node_height + 50

    def _draw_diagram(self):
        """Draw the LR(1) automaton diagram on the canvas."""
        self.diagram_canvas.delete('all')

        if not self.parser or not self.parser.states:
            self.diagram_canvas.create_text(
                400, 300, text="Build a parser to see the automaton diagram",
                font=('Segoe UI', 12), fill='gray'
            )
            return

        self._calculate_node_positions()

        # Draw start arrow pointing to initial state
        self._draw_start_arrow()

        # Draw transitions (arrows) first so they appear behind nodes
        self._draw_transitions()

        # Draw state nodes
        self._draw_nodes()

        # Update scroll region with padding
        bbox = self.diagram_canvas.bbox('all')
        if bbox:
            padding = 50
            self.diagram_canvas.configure(scrollregion=(
                bbox[0] - padding, bbox[1] - padding,
                bbox[2] + padding, bbox[3] + padding
            ))

    def _draw_start_arrow(self):
        """Draw the start arrow pointing to initial state I0."""
        if 0 not in self.node_positions or 0 not in self.node_sizes:
            return

        x, y = self.node_positions[0]
        w, h = self.node_sizes[0]

        # Apply scale and offset
        x = x * self.diagram_scale + self.diagram_offset_x
        y = y * self.diagram_scale + self.diagram_offset_y
        w = w * self.diagram_scale
        h = h * self.diagram_scale

        # Draw arrow from left side
        arrow_length = 40 * self.diagram_scale
        start_x = x - w/2 - arrow_length
        end_x = x - w/2 - 5

        self.diagram_canvas.create_line(
            start_x, y, end_x, y,
            arrow=tk.LAST, fill='black', width=2,
            arrowshape=(10, 12, 5)
        )

    def _draw_nodes(self):
        """Draw state nodes as rounded rectangles with items inside."""
        green_color = '#228B22'  # Forest green like in the reference
        font_size = 10

        for state in self.parser.states:
            if state.id not in self.node_positions:
                continue

            x, y = self.node_positions[state.id]
            w, h = self.node_sizes.get(state.id, (120, 80))

            # Apply scale and offset
            x = x * self.diagram_scale + self.diagram_offset_x
            y = y * self.diagram_scale + self.diagram_offset_y
            w = w * self.diagram_scale
            h = h * self.diagram_scale

            # Calculate box coordinates
            x1, y1 = x - w/2, y - h/2
            x2, y2 = x + w/2, y + h/2

            # Draw rounded rectangle (using polygon approximation)
            radius = 15 * self.diagram_scale
            self._draw_rounded_rect(x1, y1, x2, y2, radius,
                                   fill='#f0f8f0', outline=green_color, width=2)

            # Draw state label above/outside the box
            self.diagram_canvas.create_text(
                x, y1 - 12 * self.diagram_scale,
                text=f"I{state.id}",
                font=('Arial', int(font_size * self.diagram_scale), 'bold'),
                fill=green_color
            )

            # Draw items inside the box
            items = sorted(state.items, key=lambda item: (str(item.production), item.dot_position, item.lookahead), reverse=True)
            max_items = 8  # Limit items to prevent huge boxes
            item_y = y1 + 15 * self.diagram_scale

            for i, item in enumerate(items[:max_items]):
                # Format item as "A->.BC" style (compact format)
                item_text = self._format_item_compact(item)
                self.diagram_canvas.create_text(
                    x, item_y,
                    text=item_text,
                    font=('Consolas', int((font_size - 1) * self.diagram_scale)),
                    fill=green_color
                )
                item_y += 14 * self.diagram_scale

            # If there are more items, show "..."
            if len(items) > max_items:
                self.diagram_canvas.create_text(
                    x, item_y,
                    text=f"...+{len(items) - max_items} more",
                    font=('Consolas', int((font_size - 2) * self.diagram_scale), 'italic'),
                    fill='gray'
                )

    def _format_item_compact(self, item) -> str:
        """Format an LR(1) item in compact notation like 'A->.BC,a'"""
        prod = item.production
        right = list(prod.right)
        right.insert(item.dot_position, '.')
        right_str = ''.join(right) if right != ['.'] else '.'
        # For LR(1), include lookahead
        return f"{prod.left}->{right_str},{item.lookahead}"

    def _draw_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Draw a rounded rectangle on the canvas."""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        return self.diagram_canvas.create_polygon(points, smooth=True, **kwargs)

    def _draw_transitions(self):
        """Draw transition arrows between states."""
        arrow_color = 'black'

        for state in self.parser.states:
            if state.id not in self.node_positions:
                continue

            x1, y1 = self.node_positions[state.id]
            w1, h1 = self.node_sizes.get(state.id, (120, 80))

            x1 = x1 * self.diagram_scale + self.diagram_offset_x
            y1 = y1 * self.diagram_scale + self.diagram_offset_y
            w1 = w1 * self.diagram_scale
            h1 = h1 * self.diagram_scale

            for symbol, target_id in state.transitions.items():
                if target_id not in self.node_positions:
                    continue

                x2, y2 = self.node_positions[target_id]
                w2, h2 = self.node_sizes.get(target_id, (120, 80))

                x2 = x2 * self.diagram_scale + self.diagram_offset_x
                y2 = y2 * self.diagram_scale + self.diagram_offset_y
                w2 = w2 * self.diagram_scale
                h2 = h2 * self.diagram_scale

                # Self-loop
                if state.id == target_id:
                    self._draw_self_loop(x1, y1 - h1/2, w1, symbol)
                    continue

                # Calculate connection points on box edges
                start_x, start_y, end_x, end_y = self._calc_edge_points(
                    x1, y1, w1, h1, x2, y2, w2, h2
                )

                # Check for bidirectional transitions
                has_reverse = (target_id in self.node_positions and
                              any(t == state.id for t in self.parser.states[target_id].transitions.values()))

                # Draw curved arrow for better visibility
                if has_reverse and state.id < target_id:
                    # Curve upward
                    self._draw_curved_arrow(start_x, start_y, end_x, end_y, symbol, curve_offset=30)
                elif has_reverse and state.id > target_id:
                    # Curve downward
                    self._draw_curved_arrow(start_x, start_y, end_x, end_y, symbol, curve_offset=-30)
                else:
                    # Draw curved arrow (slight curve for aesthetics)
                    self._draw_curved_arrow(start_x, start_y, end_x, end_y, symbol, curve_offset=20)

    def _calc_edge_points(self, x1, y1, w1, h1, x2, y2, w2, h2):
        """Calculate start and end points on box edges for an arrow."""
        # Direction from center1 to center2
        dx = x2 - x1
        dy = y2 - y1

        # Start point: edge of box 1
        if abs(dx) > abs(dy):
            # Horizontal connection
            if dx > 0:
                start_x = x1 + w1/2
                end_x = x2 - w2/2
            else:
                start_x = x1 - w1/2
                end_x = x2 + w2/2
            # Calculate y based on slope
            if dx != 0:
                slope = dy / dx
                start_y = y1 + slope * (start_x - x1)
                end_y = y2 + slope * (end_x - x2)
            else:
                start_y = y1
                end_y = y2
        else:
            # Vertical connection
            if dy > 0:
                start_y = y1 + h1/2
                end_y = y2 - h2/2
            else:
                start_y = y1 - h1/2
                end_y = y2 + h2/2
            # Calculate x based on slope
            if dy != 0:
                slope = dx / dy
                start_x = x1 + slope * (start_y - y1)
                end_x = x2 + slope * (end_y - y2)
            else:
                start_x = x1
                end_x = x2

        return start_x, start_y, end_x, end_y

    def _draw_curved_arrow(self, x1, y1, x2, y2, symbol, curve_offset=20):
        """Draw a curved arrow with a label."""
        # Calculate midpoint and perpendicular offset for curve
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        # Perpendicular direction
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            # Perpendicular unit vector
            px = -dy / length
            py = dx / length
        else:
            px, py = 0, 1

        # Control point for curve
        ctrl_x = mid_x + px * curve_offset * self.diagram_scale
        ctrl_y = mid_y + py * curve_offset * self.diagram_scale

        # Draw curved line with arrow
        self.diagram_canvas.create_line(
            x1, y1, ctrl_x, ctrl_y, x2, y2,
            smooth=True, arrow=tk.LAST, fill='black', width=2,
            arrowshape=(10, 12, 5)
        )

        # Draw label near the control point
        label_x = ctrl_x
        label_y = ctrl_y - 10 * self.diagram_scale

        self.diagram_canvas.create_text(
            label_x, label_y, text=symbol,
            font=('Arial', int(10 * self.diagram_scale), 'bold'),
            fill='black'
        )

    def _draw_self_loop(self, x, y, width, symbol):
        """Draw a self-loop arrow for a state."""
        loop_radius = 25 * self.diagram_scale
        loop_center_y = y - loop_radius

        # Draw arc
        self.diagram_canvas.create_arc(
            x - loop_radius, loop_center_y - loop_radius,
            x + loop_radius, loop_center_y + loop_radius,
            start=200, extent=320, style=tk.ARC,
            outline='black', width=2
        )

        # Draw arrowhead manually
        arrow_x = x + loop_radius * 0.6
        arrow_y = loop_center_y + loop_radius * 0.8
        self.diagram_canvas.create_polygon(
            arrow_x, arrow_y,
            arrow_x - 6, arrow_y - 8,
            arrow_x + 6, arrow_y - 4,
            fill='black'
        )

        # Draw label
        self.diagram_canvas.create_text(
            x, loop_center_y - loop_radius - 8 * self.diagram_scale,
            text=symbol,
            font=('Arial', int(10 * self.diagram_scale), 'bold'),
            fill='black'
        )

    def _on_diagram_press(self, event):
        """Handle mouse press on diagram for panning."""
        self.dragging = True
        self.drag_start = (event.x, event.y)
        self.diagram_canvas.config(cursor='fleur')

    def _on_diagram_drag(self, event):
        """Handle mouse drag on diagram for panning."""
        if self.dragging:
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            self.diagram_offset_x += dx
            self.diagram_offset_y += dy
            self.drag_start = (event.x, event.y)
            self._draw_diagram()

    def _on_diagram_release(self, event):
        """Handle mouse release on diagram."""
        self.dragging = False
        self.diagram_canvas.config(cursor='')

    def _on_diagram_scroll(self, event):
        """Handle mouse scroll for zooming."""
        # Zoom in or out
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()

    def _zoom_in(self):
        """Zoom in on the diagram."""
        self.diagram_scale = min(3.0, self.diagram_scale * 1.2)
        self._draw_diagram()

    def _zoom_out(self):
        """Zoom out on the diagram."""
        self.diagram_scale = max(0.3, self.diagram_scale / 1.2)
        self._draw_diagram()

    def _reset_diagram_view(self):
        """Reset diagram view to default."""
        self.diagram_scale = 1.0
        self.diagram_offset_x = 0
        self.diagram_offset_y = 0
        self._draw_diagram()

    def _fit_diagram(self):
        """Fit diagram to window size."""
        if not self.node_positions:
            return

        # Get canvas size
        canvas_width = self.diagram_canvas.winfo_width()
        canvas_height = self.diagram_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 800
            canvas_height = 600

        # Get bounds of all nodes
        min_x = min(pos[0] for pos in self.node_positions.values())
        max_x = max(pos[0] for pos in self.node_positions.values())
        min_y = min(pos[1] for pos in self.node_positions.values())
        max_y = max(pos[1] for pos in self.node_positions.values())

        # Add padding
        padding = 100
        diagram_width = max_x - min_x + 2 * padding
        diagram_height = max_y - min_y + 2 * padding

        # Calculate scale to fit
        scale_x = canvas_width / diagram_width if diagram_width > 0 else 1
        scale_y = canvas_height / diagram_height if diagram_height > 0 else 1
        self.diagram_scale = min(scale_x, scale_y, 1.5)

        # Center the diagram
        self.diagram_offset_x = (canvas_width / 2) - ((min_x + max_x) / 2) * self.diagram_scale
        self.diagram_offset_y = (canvas_height / 2) - ((min_y + max_y) / 2) * self.diagram_scale

        self._draw_diagram()

    def _create_table_display(self, parent):
        """Create parsing table display area."""
        # Frame for the table
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill=tk.BOTH, expand=True)

        # Create Treeview for parsing table
        self.table_tree = ttk.Treeview(table_frame, show='headings')

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.table_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.table_tree.xview)
        self.table_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid layout
        self.table_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Legend
        legend_frame = ttk.LabelFrame(parent, text="Legend", padding=10)
        legend_frame.pack(fill=tk.X, pady=10)

        ttk.Label(legend_frame, text="sN = Shift to state N  |  rN = Reduce by production N  |  acc = Accept  |  N = GOTO state N",
                  font=('Segoe UI', 9)).pack()
        ttk.Label(legend_frame, text="Cells with multiple actions indicate conflicts",
                  font=('Segoe UI', 9, 'italic'), foreground='red').pack()

    def _create_conflicts_display(self, parent):
        """Create conflicts display area."""
        # Conflict summary
        self.conflict_summary = ttk.Label(parent, text="No conflicts detected.",
                                          style='Success.TLabel', font=('Segoe UI', 11))
        self.conflict_summary.pack(anchor=tk.W, pady=10)

        # Conflicts list
        self.conflicts_text = scrolledtext.ScrolledText(
            parent, height=20, font=('Consolas', 11),
            state=tk.DISABLED, wrap=tk.WORD
        )
        self.conflicts_text.pack(fill=tk.BOTH, expand=True)

        # Configure tags for coloring
        self.conflicts_text.tag_configure('conflict_header', foreground='red', font=('Consolas', 11, 'bold'))
        self.conflicts_text.tag_configure('shift_reduce', foreground='orange')
        self.conflicts_text.tag_configure('reduce_reduce', foreground='red')

    def _create_simulation_display(self, parent):
        """Create simulation display area."""
        # Current step info
        step_frame = ttk.LabelFrame(parent, text="Current Step", padding=10)
        step_frame.pack(fill=tk.X)

        self.step_info_label = ttk.Label(step_frame, text="No simulation running.",
                                         font=('Segoe UI', 11))
        self.step_info_label.pack(anchor=tk.W)

        # Stack and Input display
        display_frame = ttk.Frame(parent)
        display_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Stack
        stack_frame = ttk.LabelFrame(display_frame, text="Stack", padding=10)
        stack_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.stack_display = scrolledtext.ScrolledText(
            stack_frame, height=10, font=('Consolas', 12),
            state=tk.DISABLED, wrap=tk.WORD
        )
        self.stack_display.pack(fill=tk.BOTH, expand=True)

        # Input
        input_frame = ttk.LabelFrame(display_frame, text="Remaining Input", padding=10)
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.input_display = scrolledtext.ScrolledText(
            input_frame, height=10, font=('Consolas', 12),
            state=tk.DISABLED, wrap=tk.WORD
        )
        self.input_display.pack(fill=tk.BOTH, expand=True)

        # Simulation trace
        trace_frame = ttk.LabelFrame(parent, text="Parsing Trace", padding=10)
        trace_frame.pack(fill=tk.BOTH, expand=True)

        # Create trace table
        columns = ('step', 'stack', 'symbols', 'input', 'action')
        self.trace_tree = ttk.Treeview(trace_frame, columns=columns, show='headings', height=10)

        self.trace_tree.heading('step', text='Step')
        self.trace_tree.heading('stack', text='State Stack')
        self.trace_tree.heading('symbols', text='Symbol Stack')
        self.trace_tree.heading('input', text='Input')
        self.trace_tree.heading('action', text='Action')

        self.trace_tree.column('step', width=50, minwidth=50)
        self.trace_tree.column('stack', width=150, minwidth=100)
        self.trace_tree.column('symbols', width=150, minwidth=100)
        self.trace_tree.column('input', width=200, minwidth=150)
        self.trace_tree.column('action', width=300, minwidth=200)

        # Scrollbar
        vsb = ttk.Scrollbar(trace_frame, orient=tk.VERTICAL, command=self.trace_tree.yview)
        self.trace_tree.configure(yscrollcommand=vsb.set)

        self.trace_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure tags for trace highlighting
        self.trace_tree.tag_configure('current', background='#e6f3ff')
        self.trace_tree.tag_configure('error', background='#ffe6e6')
        self.trace_tree.tag_configure('accepted', background='#e6ffe6')

    def _build_parser(self):
        """Build the LR(1) parser from the input grammar."""
        grammar_str = self.grammar_text.get('1.0', tk.END).strip()

        if not grammar_str:
            messagebox.showwarning("Warning", "Please enter a grammar first.")
            return

        try:
            grammar = parse_grammar_text(grammar_str)

            if not grammar.productions:
                messagebox.showerror("Error", "No valid productions found in grammar.")
                return

            self.parser = LR1Parser(grammar)

            # Update displays
            self._update_grammar_display()
            self._update_states_display()
            self._update_table_display()
            self._update_conflicts_display()
            self._reset_diagram_view()  # Draw the diagram

            # Update status
            num_states = len(self.parser.states)
            num_conflicts = len(self.parser.conflicts)

            if num_conflicts > 0:
                self.status_label.config(text=f"Parser built: {num_states} states")
                self.conflict_label.config(
                    text=f"WARNING: {num_conflicts} conflict(s) detected!",
                    style='Conflict.TLabel'
                )
                self.notebook.select(self.conflicts_tab)
            else:
                self.status_label.config(text=f"Parser built successfully: {num_states} states, no conflicts")
                self.conflict_label.config(text="Grammar is LR(1)!", style='Success.TLabel')
                self.notebook.select(self.table_tab)

            # Reset simulation
            self._reset_simulation()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to build parser:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _update_grammar_display(self):
        """Update the augmented grammar display."""
        self.aug_grammar_text.config(state=tk.NORMAL)
        self.aug_grammar_text.delete('1.0', tk.END)

        # Display productions with indices
        self.aug_grammar_text.insert(tk.END, "Productions:\n\n")
        for i, prod in enumerate(self.parser.grammar.productions):
            self.aug_grammar_text.insert(tk.END, f"  {i}: {prod}\n")

        # Display FIRST sets
        self.aug_grammar_text.insert(tk.END, "\n\nFIRST Sets:\n\n")
        for nt in sorted(self.parser.grammar.non_terminals):
            first_set = self.parser.grammar.first(nt)
            first_str = ', '.join(sorted(first_set))
            self.aug_grammar_text.insert(tk.END, f"  FIRST({nt}) = {{ {first_str} }}\n")

        self.aug_grammar_text.config(state=tk.DISABLED)

        # Update symbols
        terminals = ', '.join(sorted(self.parser.grammar.terminals)) or '-'
        non_terminals = ', '.join(sorted(self.parser.grammar.non_terminals)) or '-'

        self.terminals_label.config(text=f"Terminals: {terminals}")
        self.nonterminals_label.config(text=f"Non-Terminals: {non_terminals}")

    def _update_states_display(self):
        """Update the LR(1) states display."""
        # Clear existing items
        for item in self.states_tree.get_children():
            self.states_tree.delete(item)

        # Add states
        for state in self.parser.states:
            # Group items by their core (production + dot position) for cleaner display
            items_str = ' | '.join(str(item) for item in sorted(state.items, key=lambda x: (str(x.production), x.dot_position, x.lookahead), reverse=True))
            self.states_tree.insert('', tk.END, text=f"I{state.id}",
                                    values=(items_str,), iid=str(state.id))

        # Update transitions
        self.transitions_text.config(state=tk.NORMAL)
        self.transitions_text.delete('1.0', tk.END)

        self.transitions_text.insert(tk.END, "State Transitions:\n\n")
        for state in self.parser.states:
            if state.transitions:
                for symbol, target in sorted(state.transitions.items()):
                    self.transitions_text.insert(tk.END, f"  I{state.id} --[{symbol}]--> I{target}\n")

        self.transitions_text.config(state=tk.DISABLED)

    def _update_table_display(self):
        """Update the parsing table display."""
        # Clear existing
        self.table_tree.delete(*self.table_tree.get_children())

        # Get symbols
        terminals = sorted(self.parser.grammar.terminals) + ['$']
        non_terminals = sorted(self.parser.grammar.non_terminals - {self.parser.grammar.augmented_start})

        # Configure columns
        columns = ['State'] + terminals + non_terminals
        self.table_tree['columns'] = columns

        for col in columns:
            self.table_tree.heading(col, text=col)
            width = 80 if col == 'State' else 60
            self.table_tree.column(col, width=width, minwidth=50, anchor='center')

        # Add rows
        for state in self.parser.states:
            row = [str(state.id)]

            # ACTION entries
            for terminal in terminals:
                actions = self.parser.action_table.get((state.id, terminal), [])
                cell = '/'.join(actions) if actions else ''
                row.append(cell)

            # GOTO entries
            for nt in non_terminals:
                goto = self.parser.goto_table.get((state.id, nt))
                row.append(str(goto) if goto is not None else '')

            self.table_tree.insert('', tk.END, values=row)

    def _update_conflicts_display(self):
        """Update the conflicts display."""
        conflicts = self.parser.conflicts

        if not conflicts:
            self.conflict_summary.config(text="No conflicts detected. Grammar is LR(1)!",
                                         style='Success.TLabel')
        else:
            self.conflict_summary.config(
                text=f"{len(conflicts)} conflict(s) detected. Grammar is NOT LR(1).",
                style='Conflict.TLabel'
            )

        self.conflicts_text.config(state=tk.NORMAL)
        self.conflicts_text.delete('1.0', tk.END)

        if conflicts:
            for i, conflict in enumerate(conflicts, 1):
                self.conflicts_text.insert(tk.END, f"Conflict {i}: ", 'conflict_header')
                tag = 'shift_reduce' if conflict.conflict_type == 'shift-reduce' else 'reduce_reduce'
                self.conflicts_text.insert(tk.END, f"{conflict.conflict_type.upper()}\n", tag)
                self.conflicts_text.insert(tk.END, f"  State: I{conflict.state_id}\n")
                self.conflicts_text.insert(tk.END, f"  Symbol: '{conflict.symbol}'\n")
                self.conflicts_text.insert(tk.END, f"  Actions: {', '.join(conflict.actions)}\n")
                self.conflicts_text.insert(tk.END, f"  {conflict.description}\n\n")

            self.conflicts_text.insert(tk.END, "\n" + "=" * 50 + "\n")
            self.conflicts_text.insert(tk.END, "\nExplanation:\n\n")
            self.conflicts_text.insert(tk.END, "SHIFT-REDUCE CONFLICT:\n")
            self.conflicts_text.insert(tk.END, "  The parser cannot decide whether to shift the next\n")
            self.conflicts_text.insert(tk.END, "  input symbol or reduce by a production.\n\n")
            self.conflicts_text.insert(tk.END, "REDUCE-REDUCE CONFLICT:\n")
            self.conflicts_text.insert(tk.END, "  The parser cannot decide which production to use\n")
            self.conflicts_text.insert(tk.END, "  for reduction.\n\n")
            self.conflicts_text.insert(tk.END, "These conflicts indicate the grammar is not LR(1).\n")
            self.conflicts_text.insert(tk.END, "The grammar may be inherently ambiguous.\n")
        else:
            self.conflicts_text.insert(tk.END, "The grammar has no LR(1) conflicts.\n\n")
            self.conflicts_text.insert(tk.END, "This means:\n")
            self.conflicts_text.insert(tk.END, "  - Each state has at most one action per lookahead\n")
            self.conflicts_text.insert(tk.END, "  - Reduce actions only occur for specific lookaheads\n")
            self.conflicts_text.insert(tk.END, "  - The grammar can be parsed deterministically\n")

        self.conflicts_text.config(state=tk.DISABLED)

    def _start_parsing(self):
        """Start parsing simulation with the input string."""
        if not self.parser:
            messagebox.showwarning("Warning", "Please build a parser first.")
            return

        input_str = self.input_entry.get().strip()
        if not input_str:
            messagebox.showwarning("Warning", "Please enter an input string.")
            return

        # Run parser
        self.simulation_steps = self.parser.parse(input_str)
        self.current_step = 0
        self.simulation_running = True

        # Clear trace
        self.trace_tree.delete(*self.trace_tree.get_children())

        # Add all steps to trace
        for i, step in enumerate(self.simulation_steps):
            stack_str = ' '.join(map(str, step['stack']))
            symbols_str = ' '.join(step['symbol_stack'])
            input_str = ' '.join(step['input'])
            action = step['action']

            tag = ''
            if step['status'] == 'error':
                tag = 'error'
            elif step['status'] == 'accepted':
                tag = 'accepted'

            self.trace_tree.insert('', tk.END, values=(i+1, stack_str, symbols_str, input_str, action),
                                   iid=str(i), tags=(tag,))

        # Show first step
        self._show_step(0)
        self.notebook.select(self.sim_tab)

    def _show_step(self, step_idx):
        """Display a specific simulation step."""
        if step_idx < 0 or step_idx >= len(self.simulation_steps):
            return

        step = self.simulation_steps[step_idx]
        self.current_step = step_idx

        # Update step info
        status = step['status'].upper()
        conflict_info = step.get('conflict', '')
        self.step_info_label.config(text=f"Step {step_idx + 1}/{len(self.simulation_steps)} - Status: {status} {conflict_info}")

        # Update stack display
        self.stack_display.config(state=tk.NORMAL)
        self.stack_display.delete('1.0', tk.END)
        stack_visual = "State Stack:\n"
        for i, (state, sym) in enumerate(zip(step['stack'], step['symbol_stack'])):
            stack_visual += f"  [{state}] {sym}\n"
        self.stack_display.insert(tk.END, stack_visual)
        self.stack_display.config(state=tk.DISABLED)

        # Update input display
        self.input_display.config(state=tk.NORMAL)
        self.input_display.delete('1.0', tk.END)
        input_visual = ' '.join(step['input'])
        self.input_display.insert(tk.END, f"Remaining tokens:\n\n{input_visual}\n\n")
        self.input_display.insert(tk.END, f"Action: {step['action']}")
        self.input_display.config(state=tk.DISABLED)

        # Highlight current row in trace
        for item in self.trace_tree.get_children():
            tags = list(self.trace_tree.item(item, 'tags'))
            if 'current' in tags:
                tags.remove('current')
            self.trace_tree.item(item, tags=tags)

        current_item = str(step_idx)
        tags = list(self.trace_tree.item(current_item, 'tags'))
        tags.append('current')
        self.trace_tree.item(current_item, tags=tags)
        self.trace_tree.see(current_item)

    def _step_simulation(self):
        """Advance simulation by one step."""
        if not self.simulation_steps:
            messagebox.showwarning("Warning", "Start a parsing simulation first.")
            return

        if self.current_step < len(self.simulation_steps) - 1:
            self._show_step(self.current_step + 1)

    def _auto_run(self):
        """Automatically run through all simulation steps."""
        if not self.simulation_steps:
            messagebox.showwarning("Warning", "Start a parsing simulation first.")
            return

        def run_step():
            if self.current_step < len(self.simulation_steps) - 1 and self.simulation_running:
                self._show_step(self.current_step + 1)
                self.root.after(self.speed_var.get(), run_step)

        self.simulation_running = True
        run_step()

    def _reset_simulation(self):
        """Reset the simulation state."""
        self.simulation_steps = []
        self.current_step = 0
        self.simulation_running = False

        # Clear displays
        self.trace_tree.delete(*self.trace_tree.get_children())

        self.step_info_label.config(text="No simulation running.")

        self.stack_display.config(state=tk.NORMAL)
        self.stack_display.delete('1.0', tk.END)
        self.stack_display.config(state=tk.DISABLED)

        self.input_display.config(state=tk.NORMAL)
        self.input_display.delete('1.0', tk.END)
        self.input_display.config(state=tk.DISABLED)

    def _clear_all(self):
        """Clear all input and output."""
        self.grammar_text.delete('1.0', tk.END)
        self.input_entry.delete(0, tk.END)
        self.parser = None

        # Clear displays
        self.aug_grammar_text.config(state=tk.NORMAL)
        self.aug_grammar_text.delete('1.0', tk.END)
        self.aug_grammar_text.config(state=tk.DISABLED)

        self.terminals_label.config(text="Terminals: -")
        self.nonterminals_label.config(text="Non-Terminals: -")

        for item in self.states_tree.get_children():
            self.states_tree.delete(item)

        self.transitions_text.config(state=tk.NORMAL)
        self.transitions_text.delete('1.0', tk.END)
        self.transitions_text.config(state=tk.DISABLED)

        self.table_tree.delete(*self.table_tree.get_children())
        self.table_tree['columns'] = []

        self.conflicts_text.config(state=tk.NORMAL)
        self.conflicts_text.delete('1.0', tk.END)
        self.conflicts_text.config(state=tk.DISABLED)
        self.conflict_summary.config(text="No conflicts detected.", style='Success.TLabel')

        # Clear diagram
        self.diagram_canvas.delete('all')
        self.node_positions.clear()
        self.node_sizes.clear()
        self.diagram_scale = 1.0
        self.diagram_offset_x = 0
        self.diagram_offset_y = 0

        self._reset_simulation()

        self.status_label.config(text="Ready. Enter grammar and click 'Build'.")
        self.conflict_label.config(text="")

    # Example grammars
    def _load_example_1(self):
        """Load simple expression grammar."""
        grammar = """E -> E + T
E -> T
T -> T * F
T -> F
F -> ( E )
F -> id"""
        self.grammar_text.delete('1.0', tk.END)
        self.grammar_text.insert('1.0', grammar)
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, "id + id * id")

    def _load_example_2(self):
        """Load ambiguous arithmetic grammar (causes conflicts)."""
        grammar = """E -> E + E
E -> E * E
E -> ( E )
E -> id"""
        self.grammar_text.delete('1.0', tk.END)
        self.grammar_text.insert('1.0', grammar)
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, "id + id * id")

    def _load_example_3(self):
        """Load balanced parentheses grammar."""
        grammar = """S -> ( S ) S
S -> ε"""
        self.grammar_text.delete('1.0', tk.END)
        self.grammar_text.insert('1.0', grammar)
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, "( ( ) ) ( )")

    def _load_example_4(self):
        """Load simple statement grammar."""
        grammar = """S -> if E then S else S
S -> if E then S
S -> a
E -> b"""
        self.grammar_text.delete('1.0', tk.END)
        self.grammar_text.insert('1.0', grammar)
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, "if b then a else a")

    def _load_example_5(self):
        """Load LR(1) compatible grammar (no conflicts)."""
        grammar = """S -> a A d
S -> b B d
S -> a B e
S -> b A e
A -> c
B -> c"""
        self.grammar_text.delete('1.0', tk.END)
        self.grammar_text.insert('1.0', grammar)
        self.input_entry.delete(0, tk.END)
        self.input_entry.insert(0, "a c d")

    def _show_help(self):
        """Show grammar syntax help."""
        help_text = """Grammar Syntax Help:

FORMAT:
    NonTerminal -> symbol1 symbol2 ... | alternative1 | alternative2

RULES:
    - One production per line
    - Use -> for the arrow
    - Use | to separate alternatives
    - Use spaces between symbols
    - Use epsilon or empty for epsilon production
    - First production's left side is the start symbol

CONVENTIONS:
    - Uppercase letters are typically non-terminals (E, T, F, S)
    - Lowercase letters/words are typically terminals (id, +, *, a, b)
    - The parser will automatically determine terminal/non-terminal status

EXAMPLES:
    E -> E + T | T
    T -> T * F | F
    F -> ( E ) | id
    S -> epsilon

    S -> a S b
    S -> c

LR(1) NOTES:
    - LR(1) items include a lookahead symbol: [A -> alpha . beta, a]
    - Reduce actions only apply for specific lookahead symbols
    - LR(1) can handle more grammars than LR(0) or SLR(1)
"""
        messagebox.showinfo("Grammar Syntax Help", help_text)

    def _show_about(self):
        """Show about dialog."""
        about_text = """LR(1) Parser Visualization Tool

Features:
- Grammar input with multiple productions
- Automatic grammar augmentation
- FIRST set computation
- LR(1) automaton construction with lookaheads
- Parsing table generation (ACTION & GOTO)
- Conflict detection (shift-reduce, reduce-reduce)
- Step-by-step parsing simulation
- Visual stack and input display

LR(1) Key Differences from LR(0):
- Items include lookahead: [A -> alpha . beta, a]
- Reduce actions are lookahead-specific
- Can parse larger class of grammars

Created for Compiler Design Course
"""
        messagebox.showinfo("About", about_text)


def main():
    """Main entry point."""
    root = tk.Tk()
    app = LR1ParserApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
