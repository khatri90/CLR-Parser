"""
LR(1) Parser - Tkinter User Interface
Complete visualization of LR(1) parsing with tables, states, and simulation.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional
import threading

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
        speed_scale = ttk.Scale(speed_frame, from_=100, to=2000,
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

        # Tab 3: Parsing Table
        self.table_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.table_tab, text="Parsing Table")
        self._create_table_display(self.table_tab)

        # Tab 4: Conflicts
        self.conflicts_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.conflicts_tab, text="Conflicts")
        self._create_conflicts_display(self.conflicts_tab)

        # Tab 5: Simulation
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
            items_str = ' | '.join(str(item) for item in sorted(state.items, key=lambda x: (str(x.production), x.dot_position, x.lookahead)))
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
        columns = ['State'] + [f'ACTION\n{t}' for t in terminals] + [f'GOTO\n{nt}' for nt in non_terminals]
        self.table_tree['columns'] = columns

        for col in columns:
            self.table_tree.heading(col, text=col)
            width = 80 if col == 'State' else 70
            self.table_tree.column(col, width=width, minwidth=60, anchor='center')

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
