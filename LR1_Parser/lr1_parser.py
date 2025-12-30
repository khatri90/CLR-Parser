"""
LR(1) Parser Core Logic
Implements LR(1) item generation, closure, goto, automaton construction,
parsing table generation, and conflict detection.

LR(1) items have the form [A -> alpha . beta, a] where 'a' is a lookahead symbol.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, FrozenSet
from collections import defaultdict


@dataclass(frozen=True)
class Production:
    """Represents a grammar production rule."""
    left: str
    right: Tuple[str, ...]

    def __str__(self):
        right_str = ' '.join(self.right) if self.right else 'ε'
        return f"{self.left} -> {right_str}"

    def __repr__(self):
        return str(self)


@dataclass(frozen=True)
class LR1Item:
    """
    Represents an LR(1) item.
    An item is a production with a dot at some position and a lookahead symbol.
    Example: [A -> alpha . beta, a]
    """
    production: Production
    dot_position: int
    lookahead: str  # The lookahead terminal symbol

    def __str__(self):
        right = list(self.production.right)
        right.insert(self.dot_position, '.')
        right_str = ' '.join(right) if right != ['.'] else '.'
        return f"[{self.production.left} -> {right_str}, {self.lookahead}]"

    def __repr__(self):
        return str(self)

    @property
    def is_complete(self) -> bool:
        """Check if dot is at the end (reduction item)."""
        return self.dot_position >= len(self.production.right)

    @property
    def next_symbol(self) -> Optional[str]:
        """Get symbol after the dot, or None if complete."""
        if self.is_complete:
            return None
        return self.production.right[self.dot_position]

    @property
    def rest_after_next(self) -> Tuple[str, ...]:
        """Get all symbols after the next symbol (beta in A -> alpha . B beta)."""
        if self.dot_position + 1 >= len(self.production.right):
            return ()
        return self.production.right[self.dot_position + 1:]

    def advance(self) -> 'LR1Item':
        """Create new item with dot moved one position right (same lookahead)."""
        return LR1Item(self.production, self.dot_position + 1, self.lookahead)

    def core(self) -> Tuple[Production, int]:
        """Return the core of this item (without lookahead) for comparison."""
        return (self.production, self.dot_position)


@dataclass
class LR1State:
    """Represents a state in the LR(1) automaton."""
    id: int
    items: FrozenSet[LR1Item]
    transitions: Dict[str, int] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.items)

    def __eq__(self, other):
        if isinstance(other, LR1State):
            return self.items == other.items
        return False


@dataclass
class Conflict:
    """Represents a parsing conflict."""
    state_id: int
    conflict_type: str  # 'shift-reduce' or 'reduce-reduce'
    symbol: str
    actions: List[str]
    description: str


class Grammar:
    """Represents a context-free grammar."""

    def __init__(self):
        self.productions: List[Production] = []
        self.start_symbol: Optional[str] = None
        self.augmented_start: str = "S'"
        self.non_terminals: Set[str] = set()
        self.terminals: Set[str] = set()
        self.is_augmented: bool = False
        self._first_cache: Dict[str, Set[str]] = {}

    def add_production(self, left: str, right: List[str]):
        """Add a production rule to the grammar."""
        # Handle epsilon production (ε, epsilon, or empty string means empty production)
        if right == ['ε'] or right == ['epsilon'] or right == ['']:
            right = []

        prod = Production(left, tuple(right))
        self.productions.append(prod)
        self.non_terminals.add(left)

        # First production's left side is the start symbol
        if self.start_symbol is None:
            self.start_symbol = left

        # Update terminals (symbols that are not non-terminals)
        for symbol in right:
            if symbol and not symbol.isupper() and symbol not in ['ε', 'epsilon']:
                self.terminals.add(symbol)

    def finalize(self):
        """Finalize grammar: determine terminals vs non-terminals."""
        all_symbols = set()
        for prod in self.productions:
            all_symbols.update(prod.right)

        self.terminals = all_symbols - self.non_terminals
        self.terminals.discard('')
        self._first_cache.clear()

    def augment(self):
        """Create augmented grammar with new start symbol."""
        if self.is_augmented:
            return

        # Create unique augmented start symbol
        self.augmented_start = "S'"
        while self.augmented_start in self.non_terminals:
            self.augmented_start += "'"

        # Add augmented production at the beginning
        aug_prod = Production(self.augmented_start, (self.start_symbol,))
        self.productions.insert(0, aug_prod)
        self.non_terminals.add(self.augmented_start)
        self.is_augmented = True

    def get_productions_for(self, non_terminal: str) -> List[Production]:
        """Get all productions for a given non-terminal."""
        return [p for p in self.productions if p.left == non_terminal]

    def first(self, symbol: str) -> Set[str]:
        """
        Compute FIRST set for a single symbol.
        FIRST(X) is the set of terminals that can begin strings derived from X.
        """
        if symbol in self._first_cache:
            return self._first_cache[symbol]

        result = set()

        # If terminal or $, FIRST is just the symbol itself
        if symbol in self.terminals or symbol == '$':
            result.add(symbol)
            self._first_cache[symbol] = result
            return result

        # If non-terminal, compute FIRST from productions
        if symbol in self.non_terminals:
            # Mark as being computed to handle recursion
            self._first_cache[symbol] = set()

            for prod in self.get_productions_for(symbol):
                if not prod.right:
                    # Epsilon production: add epsilon to FIRST
                    result.add('ε')
                else:
                    # Compute FIRST of the right-hand side
                    first_of_rhs = self.first_of_sequence(prod.right)
                    result.update(first_of_rhs)

            self._first_cache[symbol] = result

        return result

    def first_of_sequence(self, symbols: Tuple[str, ...]) -> Set[str]:
        """
        Compute FIRST set for a sequence of symbols.
        FIRST(X1 X2 ... Xn) considering epsilon propagation.
        """
        if not symbols:
            return {'ε'}

        result = set()
        all_have_epsilon = True

        for sym in symbols:
            first_sym = self.first(sym)
            # Add all non-epsilon symbols
            result.update(first_sym - {'ε'})

            if 'ε' not in first_sym:
                all_have_epsilon = False
                break

        if all_have_epsilon:
            result.add('ε')

        return result

    def __str__(self):
        return '\n'.join(f"{i}: {p}" for i, p in enumerate(self.productions))


class LR1Parser:
    """
    LR(1) Parser implementation.
    Builds the canonical LR(1) automaton and parsing table.
    """

    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.grammar.finalize()
        self.grammar.augment()

        self.states: List[LR1State] = []
        self.action_table: Dict[Tuple[int, str], List[str]] = defaultdict(list)
        self.goto_table: Dict[Tuple[int, str], int] = {}
        self.conflicts: List[Conflict] = []

        self._build_automaton()
        self._build_parsing_table()

    def closure(self, items: Set[LR1Item]) -> FrozenSet[LR1Item]:
        """
        Compute the closure of a set of LR(1) items.

        For each item [A -> alpha . B beta, a] in the set:
        - For each production B -> gamma
        - For each terminal b in FIRST(beta a)
        - Add [B -> . gamma, b] to the set
        """
        closure_set = set(items)
        worklist = list(items)
        
        while worklist:
            item = worklist.pop(0)
            next_sym = item.next_symbol

            if next_sym and next_sym in self.grammar.non_terminals:
                # Get beta (symbols after B in A -> alpha . B beta)
                beta = item.rest_after_next
                # Compute FIRST(beta a) where a is the lookahead
                first_beta_a = self._compute_first_beta_a(beta, item.lookahead)

                # Add all productions for B with appropriate lookaheads
                for prod in self.grammar.get_productions_for(next_sym):
                    for lookahead in first_beta_a:
                        if lookahead != 'ε':  # Don't use epsilon as lookahead
                            new_item = LR1Item(prod, 0, lookahead)
                            if new_item not in closure_set:
                                closure_set.add(new_item)
                                worklist.append(new_item)

        return frozenset(closure_set)

    def _compute_first_beta_a(self, beta: Tuple[str, ...], a: str) -> Set[str]:
        """
        Compute FIRST(beta a) for LR(1) closure.
        beta is the sequence of symbols after B in [A -> alpha . B beta, a]
        a is the lookahead of the parent item
        """
        if not beta:
            # If beta is empty, FIRST(beta a) = {a}
            return {a}

        # Compute FIRST(beta)
        first_beta = self.grammar.first_of_sequence(beta)

        if 'ε' in first_beta:
            # If epsilon in FIRST(beta), add lookahead a
            result = (first_beta - {'ε'}) | {a}
            return result
        else:
            return first_beta

    def goto(self, items: FrozenSet[LR1Item], symbol: str) -> FrozenSet[LR1Item]:
        """
        Compute GOTO(items, symbol).
        Returns closure of all items [A -> alpha X . beta, a]
        where [A -> alpha . X beta, a] is in items.
        """
        moved_items = set()

        for item in items:
            if item.next_symbol == symbol:
                moved_items.add(item.advance())

        if not moved_items:
            return frozenset()

        return self.closure(moved_items)

    def _build_automaton(self):
        """Build the LR(1) automaton (canonical collection of LR(1) item sets)."""
        # Initial state: closure of {[S' -> . S, $]}
        start_prod = self.grammar.productions[0]
        start_item = LR1Item(start_prod, 0, '$')
        initial_items = self.closure({start_item})

        initial_state = LR1State(0, initial_items)
        self.states = [initial_state]

        # Map from item sets to state IDs for quick lookup
        state_map = {initial_items: 0}

        # Process states
        worklist = [0]

        while worklist:
            state_id = worklist.pop(0)
            state = self.states[state_id]

            # Find all symbols that can be shifted
            symbols = set()
            for item in state.items:
                if item.next_symbol:
                    symbols.add(item.next_symbol)

            # Compute GOTO for each symbol
            for symbol in symbols:
                goto_items = self.goto(state.items, symbol)

                if not goto_items:
                    continue

                if goto_items in state_map:
                    # State already exists
                    target_id = state_map[goto_items]
                else:
                    # Create new state
                    target_id = len(self.states)
                    new_state = LR1State(target_id, goto_items)
                    self.states.append(new_state)
                    state_map[goto_items] = target_id
                    worklist.append(target_id)

                state.transitions[symbol] = target_id

    def _build_parsing_table(self):
        """Build ACTION and GOTO tables, detecting conflicts."""
        self.action_table.clear()
        self.goto_table.clear()
        self.conflicts.clear()

        for state in self.states:
            for item in state.items:
                if item.is_complete:
                    # Reduce action - only for the specific lookahead!
                    prod_index = self.grammar.productions.index(item.production)

                    if item.production.left == self.grammar.augmented_start:
                        # Accept action (only when lookahead is $)
                        if item.lookahead == '$':
                            if 'accept' not in self.action_table[(state.id, '$')]:
                                self.action_table[(state.id, '$')].append('accept')
                    else:
                        # Reduce by this production ONLY for this specific lookahead
                        action = f'r{prod_index}'
                        if action not in self.action_table[(state.id, item.lookahead)]:
                            self.action_table[(state.id, item.lookahead)].append(action)
                else:
                    # Shift action
                    next_sym = item.next_symbol
                    if next_sym in self.grammar.terminals:
                        if next_sym in state.transitions:
                            target = state.transitions[next_sym]
                            action = f's{target}'
                            if action not in self.action_table[(state.id, next_sym)]:
                                self.action_table[(state.id, next_sym)].append(action)

            # Fill GOTO table for non-terminals
            for symbol, target in state.transitions.items():
                if symbol in self.grammar.non_terminals:
                    self.goto_table[(state.id, symbol)] = target

        # Detect conflicts
        self._detect_conflicts()

    def _detect_conflicts(self):
        """Detect and record all conflicts in the parsing table."""
        self.conflicts.clear()

        for (state_id, symbol), actions in self.action_table.items():
            if len(actions) > 1:
                # Determine conflict type
                shifts = [a for a in actions if a.startswith('s')]
                reduces = [a for a in actions if a.startswith('r')]
                accepts = [a for a in actions if a == 'accept']

                if shifts and reduces:
                    conflict_type = 'shift-reduce'
                    desc = f"State {state_id}, symbol '{symbol}': Can either shift to state {shifts[0][1:]} or reduce by production {reduces[0][1:]}"
                elif len(reduces) > 1:
                    conflict_type = 'reduce-reduce'
                    prod_nums = [r[1:] for r in reduces]
                    desc = f"State {state_id}, symbol '{symbol}': Can reduce by productions {', '.join(prod_nums)}"
                else:
                    conflict_type = 'unknown'
                    desc = f"State {state_id}, symbol '{symbol}': Multiple actions: {actions}"

                self.conflicts.append(Conflict(
                    state_id=state_id,
                    conflict_type=conflict_type,
                    symbol=symbol,
                    actions=actions,
                    description=desc
                ))

    def parse(self, input_string: str) -> List[Dict]:
        """
        Parse input string and return step-by-step trace.
        Returns list of steps, each containing stack, input, action info.
        """
        # Tokenize input
        tokens = input_string.split() + ['$']

        steps = []
        stack = [0]  # Stack of states
        symbol_stack = ['$']  # Stack of symbols for display
        pos = 0

        while True:
            state = stack[-1]
            current_token = tokens[pos]

            # Sort actions to ensure deterministic behavior
            actions = sorted(self.action_table.get((state, current_token), []))

            step = {
                'stack': list(stack),
                'symbol_stack': list(symbol_stack),
                'input': tokens[pos:],
                'action': '',
                'status': 'parsing'
            }

            if not actions:
                step['action'] = f"Error: No action for state {state}, symbol '{current_token}'"
                step['status'] = 'error'
                steps.append(step)
                break

            # Take first action (may have conflicts)
            action = actions[0]

            if len(actions) > 1:
                step['conflict'] = f"Conflict! Multiple actions: {actions}"

            if action == 'accept':
                step['action'] = 'Accept!'
                step['status'] = 'accepted'
                steps.append(step)
                break

            elif action.startswith('s'):
                # Shift
                target_state = int(action[1:])
                step['action'] = f"Shift {current_token}, goto state {target_state}"
                steps.append(step)

                stack.append(target_state)
                symbol_stack.append(current_token)
                pos += 1

            elif action.startswith('r'):
                # Reduce
                prod_index = int(action[1:])
                prod = self.grammar.productions[prod_index]

                step['action'] = f"Reduce by {prod}"
                steps.append(step)

                # Pop |right| symbols from stack
                if prod.right:  # Not epsilon production
                    for _ in range(len(prod.right)):
                        stack.pop()
                        symbol_stack.pop()

                # GOTO
                top_state = stack[-1]
                goto_state = self.goto_table.get((top_state, prod.left))

                if goto_state is None:
                    error_step = {
                        'stack': list(stack),
                        'symbol_stack': list(symbol_stack),
                        'input': tokens[pos:],
                        'action': f"Error: No GOTO for state {top_state}, non-terminal '{prod.left}'",
                        'status': 'error'
                    }
                    steps.append(error_step)
                    break

                stack.append(goto_state)
                symbol_stack.append(prod.left)

            else:
                step['action'] = f"Unknown action: {action}"
                step['status'] = 'error'
                steps.append(step)
                break

        return steps

    def get_all_symbols(self) -> List[str]:
        """Get all symbols in order: terminals, $, non-terminals."""
        terminals = sorted(self.grammar.terminals)
        non_terminals = sorted(self.grammar.non_terminals - {self.grammar.augmented_start})
        return terminals + ['$'] + non_terminals

    def has_conflicts(self) -> bool:
        """Check if the grammar has any LR(1) conflicts."""
        return len(self.conflicts) > 0


def parse_grammar_text(text: str) -> Grammar:
    """
    Parse grammar from text format.
    Each line: A -> B C D | E F
    Alternatives separated by |
    Epsilon represented by ε or epsilon or empty (single 'e' is treated as terminal)
    """
    grammar = Grammar()

    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Parse production
        if '->' in line:
            parts = line.split('->')
        elif '→' in line:
            parts = line.split('→')
        else:
            continue

        if len(parts) != 2:
            continue

        left = parts[0].strip()
        right_side = parts[1].strip()

        # Handle alternatives
        alternatives = right_side.split('|')

        for alt in alternatives:
            alt = alt.strip()
            if alt:
                symbols = alt.split()
                # Convert epsilon representations to internal format
                # Note: Single 'e' is treated as a terminal, use 'epsilon' or 'ε' for empty
                if symbols == ['epsilon'] or symbols == ['ε']:
                    grammar.add_production(left, ['ε'])
                else:
                    grammar.add_production(left, symbols)
            else:
                grammar.add_production(left, ['ε'])

    return grammar
