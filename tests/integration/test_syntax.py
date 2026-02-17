
import sys
import os
import textwrap

# Adiciona o diretório raiz ao path para importar 'los'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from los import compile

def test_syntax(name, source, should_pass=True):
    print(f"\n--- Testing Syntax: {name} ---")
    try:
        model = compile(textwrap.dedent(source))
        if should_pass:
            print(f"✅ PASS: Compiled successfully.")
        else:
            print(f"❌ FAIL: Expected failure but compiled successfully.")
    except Exception as e:
        if should_pass:
            print(f"❌ FAIL: Expected success but failed: {e}")
        else:
            print(f"✅ PASS: Failed as expected: {e}")

if __name__ == "__main__":
    # 1. Sets and Case Sensitivity
    test_syntax("Lowercase Set with {}", """
        set S = {"A", "B"}
        var x >= 0
        minimize: x
    """)

    test_syntax("Uppercase SET (Expect Fail if case-sensitive)", """
        SET S = {"A", "B"}
        VAR x >= 0
        MINIMIZE: x
    """, should_pass=False) # I suspect strict case

    test_syntax("Set with [] (Expect Fail if grammar uses {})", """
        set S = ["A", "B"]
        var x >= 0
        minimize: x
    """, should_pass=False)

    # 2. Objective Name
    test_syntax("Objective with Name (Expect Fail)", """
        var x >= 0
        minimize Z: x
    """, should_pass=False)

    test_syntax("Objective without Name", """
        var x >= 0
        minimize: x
    """)

    # 3. Constraints
    test_syntax("Constraint Block (st:)", """
        var x >= 0
        minimize: x
        st:
            c1: x >= 1
    """)

    # 4. Declarations (Indices)
    test_syntax("Param with Iterator (Expect Fail?)", """
        set S = {"A"}
        param P[i in S]
    """, should_pass=False)

    test_syntax("Param with Set Name (Hypothesis)", """
        set S = {"A"}
        param P[S]
    """)

    test_syntax("Var with Set Name", """
        set S = {"A"}
        var x[S] >= 0
        minimize: sum(x[i] for i in S)
    """)
