"""
Quickstart Example: Solving a production optimization model with LOS.

Usage:
    python solve.py
"""
import los

result = los.solve("production.los")

if result.is_optimal:
    print(f"Status: Optimal")
    print(f"Total Cost: {result.objective}")
    print()
    print("Production Plan:")
    print(result.get_variable("qty", as_df=True))
else:
    print(f"Status: {result.status}")
