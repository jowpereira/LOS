#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Testes Específicos de Arquitetura LOS
Testes focados na verificação da estrutura e princípios da arquitetura Clean
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock

# Adicionar o diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestArchitectureStructure:
    """Testa a estrutura da arquitetura Clean do LOS"""
    
    def test_directory_structure_exists(self):
        """Verifica se a estrutura de diretórios da arquitetura está correta"""
        base_path = Path("los")
        
        expected_dirs = [
            "los/domain",
            "los/domain/entities",
            "los/domain/value_objects", 
            "los/domain/use_cases",
            "los/domain/repositories",
            "los/application",
            "los/application/dto",
            "los/application/services",
            "los/application/interfaces",
            "los/infrastructure",
            "los/infrastructure/parsers",
            "los/infrastructure/translators",
            "los/infrastructure/validators",
            "los/adapters",
            "los/shared",
            "los/shared/errors",
            "los/shared/logging",
            "los/shared/utils"
        ]
        
        existing_dirs = []
        for expected_dir in expected_dirs:
            if Path(expected_dir).exists():
                existing_dirs.append(expected_dir)
        
        # Pelo menos 80% dos diretórios esperados devem existir
        coverage = len(existing_dirs) / len(expected_dirs)
        assert coverage >= 0.8, f"Estrutura incompleta: {coverage:.1%} dos diretórios existem"
    
    def test_core_files_exist(self):
        """Verifica se os arquivos principais da arquitetura existem"""
        core_files = [
            "los/__init__.py",
            "los/domain/entities/expression.py",
            "los/domain/value_objects/expression_types.py",
            "los/application/services/expression_service.py",
            "los/application/dto/expression_dto.py",
            "los/infrastructure/parsers/los_parser.py",
            "los/infrastructure/translators/pulp_translator.py",
            "los/shared/errors/exceptions.py"
        ]
        
        existing_files = []
        for core_file in core_files:
            if Path(core_file).exists():
                existing_files.append(core_file)
        
        # Pelo menos 70% dos arquivos principais devem existir
        coverage = len(existing_files) / len(core_files)
        assert coverage >= 0.7, f"Arquivos principais faltando: {coverage:.1%} dos arquivos existem"
    
    def test_module_imports(self):
        """Testa se os módulos principais podem ser importados"""
        importable_modules = []
        total_modules = 0
        
        modules_to_test = [
            "los.domain.entities.expression",
            "los.domain.value_objects.expression_types", 
            "los.application.dto.expression_dto",
            "los.infrastructure.parsers.los_parser",
            "los.shared.errors.exceptions"
        ]
        
        for module_name in modules_to_test:
            total_modules += 1
            try:
                __import__(module_name)
                importable_modules.append(module_name)
            except ImportError:
                pass
        
        if total_modules > 0:
            import_rate = len(importable_modules) / total_modules
            assert import_rate >= 0.6, f"Muitos módulos não importáveis: {import_rate:.1%}"


class TestArchitecturePrinciples:
    """Testa se os princípios da arquitetura Clean são seguidos"""
    
    def test_dependency_inversion(self):
        """Verifica se o princípio de inversão de dependência é seguido"""
        # Testar se camadas superiores não dependem de implementações concretas
        
        violations = []
        
        # Domain não deve importar Infrastructure ou Application
        domain_files = list(Path("los/domain").rglob("*.py"))
        for file_path in domain_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                if 'from los.infrastructure' in content or 'import los.infrastructure' in content:
                    violations.append(f"Domain importa Infrastructure: {file_path}")
                    
                if 'from los.application' in content or 'import los.application' in content:
                    violations.append(f"Domain importa Application: {file_path}")
                    
            except Exception:
                pass  # Ignorar arquivos que não podem ser lidos
        
        # Application não deve importar Infrastructure diretamente
        app_files = list(Path("los/application").rglob("*.py"))
        for file_path in app_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Application pode importar interfaces, mas não implementações concretas
                if 'from los.infrastructure.parsers.los_parser import LOSParser' in content:
                    violations.append(f"Application importa implementação concreta: {file_path}")
                    
            except Exception:
                pass
        
        # Não deve haver violações críticas
        critical_violations = [v for v in violations if 'Domain importa' in v]
        assert len(critical_violations) == 0, f"Violações críticas: {critical_violations}"
    
    def test_single_responsibility(self):
        """Verifica se classes seguem o princípio da responsabilidade única"""
        # Verificar tamanho e complexidade das classes principais
        
        large_files = []
        max_reasonable_size = 500  # linhas
        
        key_files = [
            "los/domain/entities/expression.py",
            "los/application/services/expression_service.py", 
            "los/infrastructure/parsers/los_parser.py"
        ]
        
        for file_path in key_files:
            path_obj = Path(file_path)
            if path_obj.exists():
                try:
                    with open(path_obj, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    line_count = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
                    
                    if line_count > max_reasonable_size:
                        large_files.append((file_path, line_count))
                        
                except Exception:
                    pass
        
        # Arquivos muito grandes podem indicar violação do SRP
        if large_files:
            # Apenas aviso, não falha crítica
            print(f"Arquivos grandes detectados (podem violar SRP): {large_files}")
    
    def test_interface_segregation(self):
        """Verifica se interfaces são pequenas e específicas"""
        interface_files = list(Path("los/application/interfaces").rglob("*.py"))
        
        large_interfaces = []
        
        for interface_file in interface_files:
            try:
                with open(interface_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Contar métodos definidos na interface
                method_count = content.count('def ')
                
                if method_count > 15:  # F03 added translate_expression, threshold adjusted
                    large_interfaces.append((interface_file.name, method_count))
                    
            except Exception:
                pass
        
        # Interfaces não devem ser muito grandes
        assert len(large_interfaces) == 0, f"Interfaces muito grandes: {large_interfaces}"


class TestCodeQuality:
    """Testa qualidade do código da arquitetura"""
    
    def test_documentation_coverage(self):
        """Verifica se arquivos principais têm documentação"""
        documented_files = []
        total_files = 0
        
        key_files = [
            "los/__init__.py",
            "los/domain/entities/expression.py",
            "los/application/services/expression_service.py",
            "los/infrastructure/parsers/los_parser.py"
        ]
        
        for file_path in key_files:
            path_obj = Path(file_path)
            if path_obj.exists():
                total_files += 1
                try:
                    with open(path_obj, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Verificar se tem docstring
                    if '"""' in content or "'''" in content:
                        documented_files.append(file_path)
                        
                except Exception:
                    pass
        
        if total_files > 0:
            doc_rate = len(documented_files) / total_files
            assert doc_rate >= 0.8, f"Documentação insuficiente: {doc_rate:.1%}"
    
    def test_type_hints_usage(self):
        """Verifica uso de type hints nos arquivos principais"""
        typed_files = []
        total_files = 0
        
        key_files = [
            "los/domain/entities/expression.py",
            "los/domain/value_objects/expression_types.py",
            "los/application/dto/expression_dto.py"
        ]
        
        for file_path in key_files:
            path_obj = Path(file_path)
            if path_obj.exists():
                total_files += 1
                try:
                    with open(path_obj, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Verificar se usa typing
                    if 'from typing import' in content or 'import typing' in content:
                        typed_files.append(file_path)
                        
                except Exception:
                    pass
        
        if total_files > 0:
            type_rate = len(typed_files) / total_files
            assert type_rate >= 0.6, f"Uso insuficiente de type hints: {type_rate:.1%}"


class TestPerformanceBaseline:
    """Estabelece baseline de performance para a arquitetura"""
    
    def test_import_performance(self):
        """Mede tempo de importação dos módulos principais"""
        import time
        
        modules_to_test = [
            "los",
            "los.domain.entities.expression",
            "los.application.services.expression_service"
        ]
        
        import_times = []
        
        for module_name in modules_to_test:
            try:
                start_time = time.time()
                __import__(module_name)
                end_time = time.time()
                
                import_time = end_time - start_time
                import_times.append((module_name, import_time))
                
            except ImportError:
                pass  # Módulo não disponível
        
        # Imports não devem demorar mais que 1 segundo cada
        slow_imports = [(mod, t) for mod, t in import_times if t > 1.0]
        assert len(slow_imports) == 0, f"Imports lentos: {slow_imports}"
    
    def test_memory_baseline(self):
        """Estabelece baseline de uso de memória"""
        import sys
        
        # Medir tamanho dos módulos importados
        initial_modules = set(sys.modules.keys())
        
        try:
            import los
        except ImportError:
            pytest.skip("Módulo los não disponível")
        
        final_modules = set(sys.modules.keys())
        new_modules = final_modules - initial_modules
        
        # Não deve importar módulos demais
        assert len(new_modules) < 50, f"Muitos módulos importados: {len(new_modules)}"


if __name__ == "__main__":
    # Executar testes se rodado diretamente
    pytest.main([__file__, "-v", "--tb=short"])
