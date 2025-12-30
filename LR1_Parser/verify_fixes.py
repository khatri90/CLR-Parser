
import sys
import unittest
from lr1_parser import Grammar, LR1Parser, parse_grammar_text, LR1Item

class TestParserFixes(unittest.TestCase):
    def test_closure_opt(self):
        """Test if the optimized closure computation returns correct items."""
        text = "S -> A\nA -> a"
        grammar = parse_grammar_text(text)
        parser = LR1Parser(grammar)
        
        # S' -> . S, $
        start_prod = grammar.productions[0] # S' -> S
        start_item = LR1Item(start_prod, 0, '$')
        
        closure = parser.closure({start_item})
        
        # Should contain:
        # [S' -> . S, $]
        # [S -> . A, $]
        # [A -> . a, $]
        
        items_str = set(str(item) for item in closure)
        self.assertTrue(any("S' -> . S" in s for s in items_str))
        self.assertTrue(any("S -> . A" in s for s in items_str))
        self.assertTrue(any("A -> . a" in s for s in items_str))
        print("Closure test passed.")

    def test_determinism(self):
        """Test if parsing of ambiguous grammar is deterministic."""
        # Ambiguous grammar (classic if-else ambiguity)
        # S -> i S e S | i S | a
        text = """
        S -> i S e S | i S | a
        """
        grammar = parse_grammar_text(text)
        parser = LR1Parser(grammar)
        
        input_str = "i i a e a" # simple ambiguous case
        
        print(f"Conflicts found: {len(parser.conflicts)}")
        
        # Run parse multiple times
        trace1 = parser.parse(input_str)
        actions1 = [step['action'] for step in trace1]
        
        for i in range(5):
            trace_n = parser.parse(input_str)
            actions_n = [step['action'] for step in trace_n]
            
            if actions1 != actions_n:
                self.fail(f"Non-deterministic behavior detected on run {i+1}")
        
        print("Determinism test passed. Actions consistent across runs.")

if __name__ == '__main__':
    unittest.main()
