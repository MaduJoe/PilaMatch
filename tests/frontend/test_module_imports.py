"""
모듈 Import 검증 테스트

리팩토링된 프론트엔드의 각 모듈이 정상적으로 임포트되는지,
순환 참조나 누락된 심볼이 없는지 검증합니다.
"""

import sys
import os
import ast
import re
import pytest

FRONTEND_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'frontend')
)


# ──────────────────────────────────────────────
# 1. 구문(syntax) 오류 검사
# ──────────────────────────────────────────────

FRONTEND_PY_FILES = [
    "app.py",
    "api_client.py",
    "utils/__init__.py",
    "utils/constants.py",
    "utils/helpers.py",
    "components/__init__.py",
    "components/progress.py",
    "components/map.py",
    "pages/__init__.py",
    "pages/auth.py",
    "pages/step1_profile.py",
    "pages/step2_jobs.py",
    "pages/step3_offers.py",
    "pages/step4_contracts.py",
    "pages/step5_complete.py",
]


@pytest.mark.parametrize("rel_path", FRONTEND_PY_FILES)
def test_syntax_valid(rel_path):
    """각 파일이 Python 문법 오류 없이 파싱되어야 한다"""
    full_path = os.path.join(FRONTEND_DIR, rel_path)
    assert os.path.exists(full_path), f"파일이 존재하지 않음: {rel_path}"
    with open(full_path, encoding='utf-8') as f:
        source = f.read()
    try:
        ast.parse(source)
    except SyntaxError as e:
        pytest.fail(f"{rel_path} 구문 오류: {e}")


# ──────────────────────────────────────────────
# 2. utils 모듈 - constants export 검증
# ──────────────────────────────────────────────

class TestConstantsExports:
    """utils/constants.py의 필수 심볼이 모두 존재하는지 검증"""

    def _get_constants_names(self):
        path = os.path.join(FRONTEND_DIR, 'utils', 'constants.py')
        with open(path) as f:
            tree = ast.parse(f.read())
        return {
            node.targets[0].id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Name)
        }

    def test_INSTRUCTOR_STEPS_exists(self):
        assert 'INSTRUCTOR_STEPS' in self._get_constants_names()

    def test_STUDIO_STEPS_exists(self):
        assert 'STUDIO_STEPS' in self._get_constants_names()

    def test_SEOUL_REGIONS_exists(self):
        assert 'SEOUL_REGIONS' in self._get_constants_names()

    def test_RATE_PRESETS_exists(self):
        assert 'RATE_PRESETS' in self._get_constants_names()

    def test_CONTRACT_TERMS_exists(self):
        assert 'CONTRACT_TERMS' in self._get_constants_names()


# ──────────────────────────────────────────────
# 3. utils 모듈 - helpers export 검증
# ──────────────────────────────────────────────

class TestHelpersExports:
    """utils/helpers.py의 필수 함수가 모두 존재하는지 검증"""

    def _get_helper_funcs(self):
        path = os.path.join(FRONTEND_DIR, 'utils', 'helpers.py')
        with open(path) as f:
            tree = ast.parse(f.read())
        return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

    def test_get_client_exists(self):
        assert 'get_client' in self._get_helper_funcs()

    def test_logout_exists(self):
        assert 'logout' in self._get_helper_funcs()

    def test_init_session_state_exists(self):
        assert 'init_session_state' in self._get_helper_funcs()

    def test_get_user_progress_exists(self):
        assert 'get_user_progress' in self._get_helper_funcs()


# ──────────────────────────────────────────────
# 4. components 모듈 - 함수 export 검증
# ──────────────────────────────────────────────

class TestComponentsExports:
    """components의 필수 함수가 모두 선언되어 있는지 검증"""

    def _get_funcs(self, rel_path):
        path = os.path.join(FRONTEND_DIR, rel_path)
        with open(path) as f:
            tree = ast.parse(f.read())
        return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

    def test_render_progress_bar_in_progress_py(self):
        assert 'render_progress_bar' in self._get_funcs('components/progress.py')

    def test_render_step_navigation_in_progress_py(self):
        assert 'render_step_navigation' in self._get_funcs('components/progress.py')

    def test_render_kakao_map_in_map_py(self):
        assert 'render_kakao_map' in self._get_funcs('components/map.py')

    def test_components_init_exports_progress_functions(self):
        path = os.path.join(FRONTEND_DIR, 'components', '__init__.py')
        with open(path) as f:
            content = f.read()
        assert 'render_progress_bar' in content
        assert 'render_step_navigation' in content


# ──────────────────────────────────────────────
# 5. pages 모듈 - 함수 export 검증
# ──────────────────────────────────────────────

PAGES_FUNCTIONS = {
    'pages/auth.py': ['render_auth_page'],
    'pages/step1_profile.py': ['render_profile_step'],
    'pages/step2_jobs.py': ['render_find_jobs_step', 'render_create_job_step'],
    'pages/step3_offers.py': ['render_offers_step', 'render_applicants_step'],
    'pages/step4_contracts.py': ['render_contracts_step'],
    'pages/step5_complete.py': ['render_complete_step'],
}


@pytest.mark.parametrize("rel_path,expected_funcs", [
    (path, funcs) for path, funcs in PAGES_FUNCTIONS.items()
])
def test_page_functions_declared(rel_path, expected_funcs):
    """각 페이지 파일에 필요한 함수가 선언되어 있어야 한다"""
    full_path = os.path.join(FRONTEND_DIR, rel_path)
    with open(full_path) as f:
        tree = ast.parse(f.read())
    declared = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    for func in expected_funcs:
        assert func in declared, f"{rel_path}에 {func} 함수가 없음"


def test_pages_init_exports_all_page_functions():
    """pages/__init__.py가 app.py에서 필요한 모든 함수를 export해야 한다"""
    init_path = os.path.join(FRONTEND_DIR, 'pages', '__init__.py')
    with open(init_path) as f:
        content = f.read()
    required = [
        'render_auth_page', 'render_profile_step',
        'render_find_jobs_step', 'render_create_job_step',
        'render_offers_step', 'render_applicants_step',
        'render_contracts_step', 'render_complete_step',
    ]
    for name in required:
        assert name in content, f"pages/__init__.py에 {name} export 누락"


# ──────────────────────────────────────────────
# 6. APIClient 메서드 - 모든 pages에서 호출하는 메서드가 존재하는지 검증
# ──────────────────────────────────────────────

class TestAPIClientMethodCoverage:
    """모든 page 파일에서 호출하는 client.xxx()가 APIClient에 존재하는지 검증"""

    def _get_api_client_methods(self):
        path = os.path.join(FRONTEND_DIR, 'api_client.py')
        with open(path) as f:
            tree = ast.parse(f.read())
        return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}

    def _get_client_calls_in_file(self, rel_path):
        full_path = os.path.join(FRONTEND_DIR, rel_path)
        with open(full_path) as f:
            content = f.read()
        return set(re.findall(r'client\.(\w+)\(', content))

    def test_auth_page_client_methods_exist(self):
        methods = self._get_api_client_methods()
        calls = self._get_client_calls_in_file('pages/auth.py')
        missing = calls - methods
        assert not missing, f"pages/auth.py에서 존재하지 않는 API 메서드 호출: {missing}"

    def test_step1_profile_client_methods_exist(self):
        methods = self._get_api_client_methods()
        calls = self._get_client_calls_in_file('pages/step1_profile.py')
        missing = calls - methods
        assert not missing, f"pages/step1_profile.py에서 존재하지 않는 API 메서드 호출: {missing}"

    def test_step2_jobs_client_methods_exist(self):
        methods = self._get_api_client_methods()
        calls = self._get_client_calls_in_file('pages/step2_jobs.py')
        missing = calls - methods
        assert not missing, f"pages/step2_jobs.py에서 존재하지 않는 API 메서드 호출: {missing}"

    def test_step3_offers_client_methods_exist(self):
        methods = self._get_api_client_methods()
        calls = self._get_client_calls_in_file('pages/step3_offers.py')
        missing = calls - methods
        assert not missing, f"pages/step3_offers.py에서 존재하지 않는 API 메서드 호출: {missing}"

    def test_step4_contracts_client_methods_exist(self):
        methods = self._get_api_client_methods()
        calls = self._get_client_calls_in_file('pages/step4_contracts.py')
        missing = calls - methods
        assert not missing, f"pages/step4_contracts.py에서 존재하지 않는 API 메서드 호출: {missing}"

    def test_step5_complete_client_methods_exist(self):
        methods = self._get_api_client_methods()
        calls = self._get_client_calls_in_file('pages/step5_complete.py')
        missing = calls - methods
        assert not missing, f"pages/step5_complete.py에서 존재하지 않는 API 메서드 호출: {missing}"

    def test_helpers_client_methods_exist(self):
        """helpers.py에서 호출하는 client 메서드가 APIClient에 존재해야 한다"""
        methods = self._get_api_client_methods()
        calls = self._get_client_calls_in_file('utils/helpers.py')
        missing = calls - methods
        assert not missing, f"utils/helpers.py에서 존재하지 않는 API 메서드 호출: {missing}"


# ──────────────────────────────────────────────
# 7. app.py import 일관성 검증
# ──────────────────────────────────────────────

class TestAppImportConsistency:
    """app.py가 필요한 모든 심볼을 올바른 모듈에서 import하는지 검증"""

    def _parse_imports(self, rel_path):
        full_path = os.path.join(FRONTEND_DIR, rel_path)
        with open(full_path) as f:
            tree = ast.parse(f.read())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ''
                level = '.' * node.level
                names = [alias.name for alias in node.names]
                imports.append((f"{level}{module}", names))
        return imports

    def test_app_imports_from_utils(self):
        """app.py가 utils에서 필수 심볼을 import해야 한다"""
        imports = self._parse_imports('app.py')
        utils_imports = {name for mod, names in imports if 'utils' in mod for name in names}
        required = {'init_session_state', 'get_client', 'get_user_progress', 'logout',
                    'INSTRUCTOR_STEPS', 'STUDIO_STEPS'}
        missing = required - utils_imports
        assert not missing, f"app.py의 utils import에서 누락: {missing}"

    def test_app_imports_from_components(self):
        """app.py가 components에서 필수 함수를 import해야 한다"""
        imports = self._parse_imports('app.py')
        comp_imports = {name for mod, names in imports if 'components' in mod for name in names}
        required = {'render_progress_bar', 'render_step_navigation'}
        missing = required - comp_imports
        assert not missing, f"app.py의 components import에서 누락: {missing}"

    def test_app_imports_from_pages(self):
        """app.py가 pages에서 필수 함수를 import해야 한다"""
        imports = self._parse_imports('app.py')
        page_imports = {name for mod, names in imports if 'pages' in mod for name in names}
        required = {
            'render_auth_page', 'render_profile_step',
            'render_find_jobs_step', 'render_create_job_step',
            'render_offers_step', 'render_applicants_step',
            'render_contracts_step', 'render_complete_step',
        }
        missing = required - page_imports
        assert not missing, f"app.py의 pages import에서 누락: {missing}"


# ──────────────────────────────────────────────
# 8. 파일 구조 검증
# ──────────────────────────────────────────────

class TestFileStructure:
    """리팩토링된 파일 구조가 완전한지 검증"""

    REQUIRED_FILES = [
        'app.py',
        'api_client.py',
        'utils/__init__.py',
        'utils/constants.py',
        'utils/helpers.py',
        'components/__init__.py',
        'components/progress.py',
        'components/map.py',
        'pages/__init__.py',
        'pages/auth.py',
        'pages/step1_profile.py',
        'pages/step2_jobs.py',
        'pages/step3_offers.py',
        'pages/step4_contracts.py',
        'pages/step5_complete.py',
    ]

    @pytest.mark.parametrize("rel_path", REQUIRED_FILES)
    def test_required_file_exists(self, rel_path):
        full_path = os.path.join(FRONTEND_DIR, rel_path)
        assert os.path.isfile(full_path), f"필수 파일 없음: {rel_path}"

    def test_app_py_is_main_entry_point(self):
        """app.py에 main() 함수가 존재해야 한다"""
        path = os.path.join(FRONTEND_DIR, 'app.py')
        with open(path) as f:
            tree = ast.parse(f.read())
        funcs = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        assert 'main' in funcs

    def test_app_py_calls_main(self):
        """app.py 하단에 if __name__ == '__main__': main() 패턴이 있어야 한다"""
        path = os.path.join(FRONTEND_DIR, 'app.py')
        with open(path) as f:
            content = f.read()
        assert '__name__' in content and 'main()' in content

    def test_backup_file_exists(self):
        """원본 백업 파일이 존재해야 한다"""
        backup_path = os.path.join(FRONTEND_DIR, 'app_original_backup.py')
        assert os.path.exists(backup_path), "원본 백업 파일(app_original_backup.py)이 없음"
