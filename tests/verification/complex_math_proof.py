import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from los.infrastructure.parsers.los_parser import LOSParser
from los.infrastructure.translators.pulp_translator import PuLPTranslator
from los.domain.entities.expression import Expression

def verify():
    parser = LOSParser()
    translator = PuLPTranslator()

    # Complex model with:
    # 1. Sets and Ranges
    # 2. Parameters with escaped strings (Windows paths, nested quotes)
    # 3. Variables with domains
    # 4. Objective with Power (^2), Aggregation (SUM), and arithmetic
    # 5. Constraints with Conditional logic (where), nested loops, and comparisons
    complex_model = r"""
    # Explicit import with Windows path (supported by translator)
    import "C:\\Windows\\System32\\drivers\\etc\\hosts" 
    
    set I = 1..5
    set J = {"Alpha", "Beta", "Gamma"}
    
    param Cost[I]
    param Config = "Path: 'C:\\Windows\\System32'; Mode: \"Advanced\""
    
    var x[I] : continuous >= 0
    var y[J] : bin

    # Mathematical Objective: Non-linear term (x^2) mixed with linear
    maximize: sum(x[i] * (Cost[i] + 10.5)^2 for i in I) - sum(y[j] * 50 for j in J)

    subject to:
        # Nested Sum + Filter
        # Constraint loops over I (forall i in I)
        c1: sum(x[i] * y[j] for j in J where j != "Beta") <= 100.0 for i in I
        
        # If expression
        c2: x[1] + (if(y["Alpha"] == 1, 10, 0)) >= 5
    """

    print("Parsing complex model...")
    try:
        parse_result = parser.parse(complex_model)
        print("Parsing successful.")
    except Exception as e:
        print(f"Parsing FAILED: {e}")
        return

    expr = Expression(complex_model)
    expr.syntax_tree = parse_result['parsed_result']
    
    print("Translating complex model...")
    try:
        python_code = translator.translate_expression(expr)
        print("Translation successful.")
    except Exception as e:
        print(f"Translation FAILED: {e}")
        return
    
    print("\n--- GENERATED PULP CODE ---\n")
    print(python_code)
    print("\n---------------------------\n")

    # Verify string robustness
    # The generated code should contain the safe python string representation
    if "C:\\Windows\\System32" in python_code or 'C:\\\\Windows\\\\System32' in python_code:
        print("[CHECK] file path string preserved correctly.")
    else:
        print("[FAIL] file path string mangled.")

    if "Advanced" in python_code:
        print("[CHECK] nested quotes preserved correctly.")
    else:
        print("[FAIL] nested quotes mangled.")

if __name__ == "__main__":
    verify()
