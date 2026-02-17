"""Repositórios em memória para testes."""

from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ...domain.entities.expression import Expression
from ...domain.repositories.interfaces import IExpressionRepository, IGrammarRepository


class InMemoryExpressionRepository(IExpressionRepository):
    """Repositório de expressões em memória."""
    
    def __init__(self):
        self._store: Dict[UUID, Expression] = {}
    
    def save(self, expression: Expression) -> Expression:
        if not expression.id:
            expression.id = uuid4()
        self._store[expression.id] = expression
        return expression
    
    def find_by_id(self, expression_id: UUID) -> Optional[Expression]:
        return self._store.get(expression_id)
    
    def find_by_type(self, expression_type: str) -> List[Expression]:
        return [
            expr for expr in self._store.values()
            if expr.expression_type.value == expression_type
        ]
    
    def find_all(self) -> List[Expression]:
        return list(self._store.values())
    
    def delete(self, expression_id: UUID) -> bool:
        if expression_id in self._store:
            del self._store[expression_id]
            return True
        return False
    
    def count(self) -> int:
        return len(self._store)
    
    def clear(self):
        """Helper for testing — clears all stored expressions."""
        self._store.clear()


class InMemoryGrammarRepository(IGrammarRepository):
    """Repositório de gramáticas em memória."""
    
    def __init__(self, grammar_dir: Optional[str] = None):
        self._grammars: Dict[str, str] = {}
        self._grammar_dir = grammar_dir
    
    def load_grammar(self, grammar_name: str = "los_grammar") -> str:
        if grammar_name in self._grammars:
            return self._grammars[grammar_name]
        
        # Try loading from filesystem
        if self._grammar_dir:
            import os
            path = os.path.join(self._grammar_dir, f"{grammar_name}.lark")
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self._grammars[grammar_name] = content
                return content
        
        return ""
    
    def save_grammar(self, grammar_name: str, content: str) -> bool:
        self._grammars[grammar_name] = content
        return True
    
    def list_grammars(self) -> List[str]:
        return list(self._grammars.keys())
