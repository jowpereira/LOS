
import sys
import os
import textwrap
import pandas as pd

# Adiciona o diretório raiz ao path para importar 'los'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from los import compile, solve

def create_csvs():
    """Creates CSV files needed for documentation examples."""
    with open("products.csv", "w") as f:
        f.write("Products,Cost\nWidgetA,10\nWidgetB,15\n")
        
    with open("factories.csv", "w") as f:
        f.write("Factories,Capacity\nFactory1,1000\nFactory2,2000\n")

    # Create dummy data/ folder for MANUAL example
    if not os.path.exists("data"):
        os.makedirs("data")
    with open("data/products.csv", "w") as f:
        f.write("Products,Cost\nWidgetA,10\nWidgetB,15\n")
    with open("data/factories.csv", "w") as f:
        f.write("Factories,Capacity\nFactory1,1000\nFactory2,2000\n")

def verify_snippet(name, los_code, data=None):
    print(f"\n--- Verifying Doc Snippet: {name} ---")
    model = None
    try:
        print("Compiling...")
        model = compile(los_code, data=data) 
        
        print("Solving...")
        result = model.solve()
        
        if "Error" in str(result.status):
            print(f"❌ FAIL: Status: {result.status}")
            print(f"--- Generated Code ---\n{model.python_code}\n----------------------")
        else:
            print(f"✅ PASS: Solved with status: {result.status}")
            
    except Exception as e:
        print(f"❌ FAIL: {e}")
        if model:
             print(f"--- Generated Code ---\n{model.python_code}\n----------------------")
        # Print code with line numbers for debug
        for i, line in enumerate(los_code.split('\n')):
            print(f"{i+1}: {line}")

if __name__ == "__main__":
    create_csvs()
    
    # 1. README Example: Production Planning (Native Import)
    readme_example = """
    # 1. Import Data
    import "products.csv"
    import "factories.csv"

    # 2. Sets (Populated from CSVs)
    set Products
    set Factories

    # 3. Parameters (Populated from CSVs)
    param Cost[Products]
    param Capacity[Factories]

    # 4. Variables
    var qty[Products, Factories] >= 0

    # 5. Objective
    minimize: 
        sum(qty[p,f] * Cost[p] for p in Products, f in Factories)

    # 6. Constraints
    subject to:
        limit: 
            sum(qty[p,f] for p in Products) <= Capacity[f]
            for f in Factories
    """
    
    # Note: No data dict needed, imports handle it!
    verify_snippet("README - Native Import", readme_example)

    # 2. MANUAL Example 1: Basic Usage (No Import)
    manual_basic = """
    set I = {"A", "B"}
    var x[I] >= 0
    maximize: sum(x[i] for i in I)
    subject to:
        limit: sum(x[i] for i in I) <= 10
    """
    verify_snippet("MANUAL - Basic Usage", manual_basic)
    
    # 3. MANUAL Example 2: Imports
    manual_import = """
    import "data/products.csv"
    import "data/factories.csv"
    set Products
    set Factories
    param Cost[Products]
    """
    verify_snippet("MANUAL - Imports", manual_import)
