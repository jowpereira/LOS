import pytest
from lark import Lark

# Load grammar content directly for testing or load from file
with open("los/los_grammar.lark", "r") as f:
    GRAMMAR = f.read()

parser = Lark(GRAMMAR, start="statement", parser="lalr")

def test_imports():
    """Test import statements in EN and PT"""
    assert parser.parse('import "model.los"')
    assert parser.parse('importar "modelo.los"')

def test_sets():
    """Test set declarations"""
    # Literal
    assert parser.parse('set P = {A, B, C}')
    assert parser.parse('conj P = {A, B, C}')
    # Range
    assert parser.parse('set T = 1..10')
    assert parser.parse('set T = 1..10 step 2')
    # Filter
    assert parser.parse('set P = {p in Produtos where custo > 100}')

def test_params():
    """Test parameter declarations"""
    assert parser.parse('param custo[P]')
    assert parser.parse('param demanda[P, L] = 100')

def test_vars():
    """Test variable declarations"""
    # Simple
    assert parser.parse('var x >= 0')
    # Indexed
    assert parser.parse('var x[P, L] >= 0')
    # Typed
    assert parser.parse('var y[P] : int >= 0')
    assert parser.parse('var z[L] : bin')
    # PT-BR types
    assert parser.parse('var w[P] : inteiro >= 0')
    assert parser.parse('var k : binario')

def test_objective():
    """Test objective functions"""
    # English
    assert parser.parse('min: sum(x[p] for p in P)')
    assert parser.parse('maximize: 10 * x + y')
    # Portuguese
    assert parser.parse('minimizar: soma(x[p] para p em P)')
    assert parser.parse('max: x + y')

def test_constraints():
    """Test constraint blocks"""
    model = """
    st:
        demanda[p]: x[p] >= 100 for p in P
        capacidade: x[p] <= 500 for p in P
    """
    assert parser.parse(model)

    model_pt = """
    sujeito a:
        rest1: x + y <= 10
        rest2: x >= 0
    """
    assert parser.parse(model_pt)

def test_comprehensions():
    """Test loop comprehensions"""
    # English
    assert parser.parse('min: sum(x[i] for i in I)')
    assert parser.parse('min: sum(x[i,j] for i in I, j in J)')
    assert parser.parse('min: sum(x[i] for i in I where i > 0)')
    
    # Portuguese
    assert parser.parse('min: soma(x[i] para i em I)')
    assert parser.parse('min: soma(x[i] para i em I onde i > 0)')

def test_inline_if():
    """Test inline if"""
    assert parser.parse('min: if(x > 0, 10, 0)')
    assert parser.parse('min: se(x > 0, 10, 0)')
