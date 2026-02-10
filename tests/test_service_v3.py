
import pytest
from unittest.mock import MagicMock
from los.application.services.expression_service import ExpressionService
from los.application.dto.expression_dto import ExpressionRequestDTO
from los.domain.entities.expression import Expression
from los.shared.errors.exceptions import InternalError, LOSError

from los.domain.value_objects.expression_types import Variable, ExpressionType

class TestExpressionServiceIntegration:
    
    def setup_method(self):
        # Mocks
        self.expression_repo = MagicMock()
        self.grammar_repo = MagicMock()
        self.parser_adapter = MagicMock()
        self.translator_adapter = MagicMock()
        self.validator_adapter = MagicMock()
        
        self.service = ExpressionService(
            expression_repository=self.expression_repo,
            grammar_repository=self.grammar_repo,
            parser_adapter=self.parser_adapter,
            translator_adapter=self.translator_adapter,
            validator_adapter=self.validator_adapter
        )

    def test_parse_expression_calls_translator(self):
        # Setup successful parse
        text = "min: x"
        
        # Mock Variable object
        var_x = Variable(name="x", variable_type="continuous")
        
        # Parser returns dict
        self.parser_adapter.parse.return_value = {
            'parsed_result': {'type': 'objective', 'expression': 'x'},
            'variables': [var_x],
            'datasets': []
        }
        
        # Repository save return
        saved_expr = Expression(original_text=text)
        saved_expr.id = "123"
        self.expression_repo.save.return_value = saved_expr
        
        # Execute
        request = ExpressionRequestDTO(text=text, save_result=True)
        response = self.service.parse_expression(request)
        
        # Assert Translation was called
        # The service calls translator.translate_expression(expression_entity)
        self.translator_adapter.translate_expression.assert_called_once()
        
        # Verify success
        assert response.success is True
        # Note: python_code in response depends on the mock modifying the expression object in place.
        # Since MagicMock doesn't modify the entity unless we tell side_effect to, python_code might be empty 
        # but the CALL is verified.

    def test_translation_failure_handled(self):
        # Setup parser success
        self.parser_adapter.parse.return_value = {'parsed_result': {'type': 'model'}, 'variables': []}
        
        # Setup translator failure
        self.translator_adapter.translate_expression.side_effect = Exception("Translation Boom")
        
        # Execute
        request = ExpressionRequestDTO(text="import 'x'", save_result=False)
        response = self.service.parse_expression(request)
        
        # Assert failure/warning
        assert response.success is False # We decided to fail logic in step 730
        assert "Translation Error: Translation Boom" in response.errors[0]

    def test_internal_error_usage(self):
        # Just verify we can instantiate InternalError
        err = InternalError("Test Internal")
        assert isinstance(err, LOSError)
        assert err.error_code == 'INTERNAL_ERROR'

from los.infrastructure.parsers.los_parser import LOSParser
from los.infrastructure.translators.pulp_translator import PuLPTranslator

class TestExpressionServiceE2E:
    
    def setup_method(self):
        # Real Adapters
        self.parser = LOSParser()
        self.translator = PuLPTranslator()
        
        # Mocks for Repos only
        self.expression_repo = MagicMock()
        self.grammar_repo = MagicMock()
        self.validator = MagicMock()
        
        # Initialize Service with Real Core components
        self.service = ExpressionService(
            expression_repository=self.expression_repo,
            grammar_repository=self.grammar_repo,
            parser_adapter=self.parser,
            translator_adapter=self.translator,
            validator_adapter=self.validator
        )

    def test_e2e_full_model_translation(self):
        LOS_MODEL = """
        var x >= 0
        min: 2*x
        st:
            limit: x <= 10
        """
        
        request = ExpressionRequestDTO(text=LOS_MODEL, save_result=True)
        response = self.service.parse_expression(request)
        
        if not response.success:
            print(f"E2E Failed. Errors: {response.errors}")
            print(f"Validation Errors: {response.validation_errors}")
            
        # Verify Success
        assert response.success is True
        assert response.is_valid is True
        
        # Verify Python Code Generated
        code = response.python_code
        assert "import pulp" in code
        assert "prob = pulp.LpProblem" in code
        assert "x = pulp.LpVariable" in code
        # Code generation might vary in spacing
        # Check for key elements. Note _visit_binary_op adds parens.
        # min: 2*x -> prob += (2 * x) or (2.0 * x)
        assert "prob += (2" in code and "* x)" in code
        assert "x <= 10" in code
        assert "prob.solve()" in code

    def test_e2e_sanitization(self):
        # R09/C04 Check via Service
        BAD_IMPORT = "import \"file');rm -rf /; .csv\""
        request = ExpressionRequestDTO(text=BAD_IMPORT, save_result=False)
        response = self.service.parse_expression(request)
        
        # Should succeed parsing/translating (sanitized)
        assert response.success is True
        code = response.python_code
        # Check that quotes were removed, preventing injection
        assert "');" not in code
        # Check that it generated a read_csv call
        assert "pd.read_csv" in code
        # 'rm -rf' IS in the string content, but safely inside quotes


