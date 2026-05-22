import subprocess
import time
import sys
from pathlib import Path
import shutil # for deleting src back
import re
import pytest


test_program_files_data = [
    ('dist/__init__.py', ''),
    ('dist/README.md', 'This is a test program, auto-created by script'),
    ('src/__init__.py', ''),
    ('src/module2.py', '\n# some complicated code goes here, that must be tricky to put into bundle and escape in quoted strings\n\n# \'\'\'\'\'\'\'\'\'\'\n\n# """""""""\n\ntxt = "hello\\\\\\\\\\\'\\\'\\\'\\\\\\\'\\\'\\\' \\\'\\\'\\\'yes"\n\na1 = \'\'\'\nhello\n\\\'\'\'inner triple-quoted content\n\\\\\\\'\'\'inner triple-quoted content\n\'\'\'\n\nb1 = """\nhi \'\'\'warrior\'\'\'\n\\"""inner triple-quoted content\\"""\n\\\\\\"""inner triple-quoted content\\\\\\"""\n"""\n\na2 = r\'\'\'\nhello\n\\\'\'\\\'not possible\n\\\\\'\'\\\'not possible\n\\\\\\\'\'\\\'not possible\n\'\'\'\n\nb2 = r"""\nhi \'\'\'warrior\'\'\'\n\\""\\"not possible\\""\\"\n\\\\""\\"not possible\\\\""\\"\n\\\\\\""\\"not possible\\\\\\""\\"\n"""\n\na1_repr = "\\nhello\\n\'\'\'inner triple-quoted content\\n\\\\\'\'\'inner triple-quoted content\\n"\nb1_repr = \'\\nhi \\\'\\\'\\\'warrior\\\'\\\'\\\'\\n"""inner triple-quoted content"""\\n\\\\"""inner triple-quoted content\\\\"""\\n\'\na2_repr = "\\nhello\\n\\\\\'\'\\\\\'not possible\\n\\\\\\\\\'\'\\\\\'not possible\\n\\\\\\\\\\\\\'\'\\\\\'not possible\\n"\nb2_repr = \'\\nhi \\\'\\\'\\\'warrior\\\'\\\'\\\'\\n\\\\""\\\\"not possible\\\\""\\\\"\\n\\\\\\\\""\\\\"not possible\\\\\\\\""\\\\"\\n\\\\\\\\\\\\""\\\\"not possible\\\\\\\\\\\\""\\\\"\\n\'\n'),
    ('src/launcher.py', 'import argparse\nimport traceback, sys\n\n\n\n# import json\n\n\n\nimport_recursive_failed = False\nif __name__ == \'__main__\':\n    # run as a program\n    import module2\n    from module3 import hello\nelif \'.\' in __name__:\n    # package\n    from . import module2\n    from .module3 import hello\nelse:\n    # included with no parent package\n    import module2\n    from module3 import hello\ntry:\n    if __name__ == \'__main__\':\n        # run as a program\n        from recursive.bundle import launcher as launcher_recursive\n    elif \'.\' in __name__:\n        # package]\n        from .recursive.bundle import launcher as launcher_recursive\n    else:\n        # included with no parent package\n        from recursive.bundle import launcher as launcher_recursive\nexcept ImportError as e:\n    import_recursive_failed = e\n\n\n\n# STDOUT_COLOR_RED = "\\033[91m"\nSTDOUT_COLOR_RED = "\\033[31m"\nSTDOUT_COLOR_RESET = "\\033[0m"\nSTDOUT_COLOR_GREEN = "\\033[32m"\n\n\n\n\n\n\n\n\ndef call_test_program(*argcs,**kwargs):\n    msg = \'\'\'\nHello, world from test program!\n    \'\'\'\n    print(msg)\n    return True\n\ndef call_module2_program(*argcs,**kwargs):\n    # print(module2.__file__)\n    # print(dir(module2))\n    print(module2.a1)\n    print(module2.b1)\n    print(module2.a2)\n    print(module2.b2)\n    print((module2.a1_repr))\n    print((module2.b1_repr))\n    print((module2.a2_repr))\n    print((module2.b2_repr))\n    print(f\'txt == {repr(module2.txt)}\')\n    assert module2.a1==module2.a1_repr, \'module2 test failed: a1 !== a1_repr\'\n    assert module2.b1==module2.b1_repr, \'module2 test failed: b1 !== b1_repr\'\n    assert module2.a2==module2.a2_repr, \'module2 test failed: a2 !== a2_repr\'\n    assert module2.b2==module2.b2_repr, \'module2 test failed: b2 !== b2_repr\'\n    return True\n\ndef call_module3_program(*argcs,**kwargs):\n    print(hello.exec_my_code(hello.code))\n    return True\n\ndef call_recursive_pinlined_import_program(*argcs,**kwargs):\n    if import_recursive_failed:\n        raise e\n    result = launcher_recursive.call_test_program()\n    return result\n\n\n\nrun_programs = {\n    \'test\': call_test_program,\n    \'module2\': call_module2_program,\n    \'module3\': call_module3_program,\n    \'recursive\': call_recursive_pinlined_import_program,\n}\n\n\n\ndef main(args_inp=None):\n    try:\n        parser = argparse.ArgumentParser(\n            description="Universal caller of mdmtoolsap-py utilities"\n        )\n        parser.add_argument(\n            #\'-1\',\n            \'--program\',\n            choices=dict.keys(run_programs),\n            type=str,\n            required=True\n        )\n        args = None\n        args_rest = None\n        try:\n            args, args_rest = parser.parse_known_args() if args_inp is None else parser.parse_known_args(args_inp)\n        except SystemExit as e:\n            print(f\'{STDOUT_COLOR_RED}Error: Invalid command-line arguments{STDOUT_COLOR_RESET}\',file=sys.stderr)\n            raise e\n        if args.program:\n            program = \'{arg}\'.format(arg=args.program)\n            if program in run_programs:\n                run_programs[program](args_rest)\n            else:\n                raise AttributeError(\'program to run not recognized: {program}\'.format(program=args.program))\n        else:\n            print(\'program to run not specified\')\n            raise AttributeError(\'program to run not specified\')\n    except Exception as e:\n        # the program is designed to be user-friendly\n        # that\'s why we reformat error messages a little bit\n        # stack trace is still printed (I even made it longer to 20 steps!)\n        # but the error message itself is separated and printed as the last message again\n\n        # for example, I don\'t write "print(\'File Not Found!\');exit(1);", I just write "raise FileNotFoundErro()"\n        print(\'\',file=sys.stderr)\n        print(\'Stack trace:\',file=sys.stderr)\n        print(\'\',file=sys.stderr)\n        traceback.print_exception(e,limit=20)\n        print(\'\',file=sys.stderr)\n        print(\'\',file=sys.stderr)\n        print(\'\',file=sys.stderr)\n        print(\'Error:\',file=sys.stderr)\n        print(\'\',file=sys.stderr)\n        print(f\'{STDOUT_COLOR_RED}{e}{STDOUT_COLOR_RESET}\',file=sys.stderr)\n        print(\'\',file=sys.stderr)\n        exit(1)\n\n\nif __name__ == \'__main__\':\n    main()\n'),
    ('src/module3/hello.py', '\n# some complicated code goes here, that must be tricky to put into bundle and escape in quoted strings\n\ntriquo_start = "r\'\'"+"\'\\n"\ntriquo_end = "\\n\'"+"\'\'"\n\ncode = \'\'\'\ntriquo_start = "r\'\'"+"\'\\\\n"\ntriquo_end = "\\\\n\'"+"\'\'"\nresult = f\'{triquo_start}Hello{triquo_end}\'\n\'\'\'\n\ndef exec_my_code(txt):\n    scope = {}\n    exec(txt,scope)\n    return scope[\'result\']\n'),
    ('src/module3/__init__.py', ''),
    ('src/recursive/__init__.py', ''),
]



def scan_and_capture_program_files(path):
    """Use this to generate the test_program_files_data """
    root = Path(path)
    excluded = {".git", "__pycache__",".DS_Store"}

    files_data = []

    for path in root.rglob("*"):
        if path.is_file():
            if any(part in excluded for part in path.parts):
                continue
            try:
                rel_path = path.relative_to(root)
                content = None
                try:
                    content = path.read_text(encoding="utf-8")
                except Exception as e:
                    print(f'Failed reading {path}: {e}',file=sys.stdout)
                    content = None

                files_data.append((str(rel_path), content))
            except Exception as e:
                print(f'Failed processing {path}: {e}',file=sys.stdout)
                raise e

    return files_data

def write_test_program_files(path):
    """Use this to create physical files for the test program on disk
    The source for files is test_program_files_data
    And the target is tmp_path (assuming all we create is in src/)
    """

    output_root = Path(path).resolve()
    print(f'Creating test program files in {output_root}...')
    n_processed = 0

    for rel_path, content in test_program_files_data:
        file_path = output_root / rel_path

        # Create parent folders automatically
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_path.write_text(content, encoding="utf-8")
        n_processed += 1

    print(f'{n_processed} files written')



def check_test_output_correct(output):
    """Individual tests to check outputs from specific programs"""
    # assert re.match()
    msg = 'Hello, world from test program!'
    assert msg in output, f'Error: output does not include the expected string\n=== EXPECTED ===\n{msg}\n=== END EXPECTED ===\n=== ACTUAL OUTPUT ===\n{output}\n=== END OUTPUT ===\n'

def check_txt_repr_in_module2(output):
    """Individual tests to check outputs from specific programs"""
    txt = "hello\\\\\'\'\'\\\'\'\' \'\'\'yes"
    msg = f'txt == {repr(txt)}'
    assert msg in output, f'Error: output does not include the expected string\n=== EXPECTED ===\n{msg}\n=== END EXPECTED ===\n=== ACTUAL OUTPUT ===\n{output}\n=== END OUTPUT ===\n'

verify_result_tests = [
    ('test',check_test_output_correct),
    ('module2',check_txt_repr_in_module2),
]


ROOT_PROJECT = Path(__file__).resolve().parents[1]


def tst(tmp_path,pinliner_added_args:list[str],program_to_test:str):
    """Run the test, as specified in arguments"""

    # Step 0: prepare constants
    project_dir = ROOT_PROJECT.resolve()
    pinliner_executable = (ROOT_PROJECT / "pinliner/pinliner.py").resolve()
    python_executable = Path(sys.executable).resolve()
    output_bundle = (tmp_path / 'dist' / 'test_bundle.py').resolve()
    print(f'for debugging:\ntmp_path == {tmp_path},\nproject_dir == {repr(project_dir)},\npinliner_executable == {repr(pinliner_executable)},\npython_executable == {repr(python_executable)},\noutput_bundle == {repr(output_bundle)}\n')

    # Step 1. Create test program in tmp_path
    print('creating temporary program for testing in tml folder...')
    write_test_program_files(tmp_path)
    print('Verify temp program exists...')
    expected_test_program_module = tmp_path / 'src' / 'launcher.py'
    if True:
        def s(t):
            return f'{t}'
        print(f'list files in tmp_path:\n{tmp_path}\n{"\n".join([s(tmp_path/path[0]) for path in scan_and_capture_program_files(tmp_path)])}')
    assert expected_test_program_module.exists(), "Error: test program was not created"
    print('done')

    # Step 2.pre. Run pinliner on recursive sub-bundle, if tested feature is "recursive"
    if program_to_test in ['recursive']:
        print('Creating sub-bundle: calling pinliner...')
        output_subbundle = (tmp_path / 'src' / 'recursive' / 'bundle.py').resolve()
        print('Calling pinliner...')
        print('Verify bundle exists (it should not)...')
        assert not output_subbundle.exists(), f'Failed (bundle already exists before calling pinliner ({output_subbundle})'
        args = [python_executable, pinliner_executable, "src", "-o", output_subbundle]+pinliner_added_args
        print(f'calling pinliner with the following args: {repr(args)}')
        pinliner_subbundle = subprocess.run(
            args,
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert pinliner_subbundle.returncode == 0, f'Failed:\nreturncode == {repr(pinliner_subbundle.returncode)},\n=== STDERR ===\n{pinliner_subbundle.stderr}\n=== END OF STDERR ===\n=== STDOUT ===\n{pinliner_subbundle.stdout}\n=== END OF STDOUT ===\n'
        print('Verify bundle exists...')
        if not output_subbundle.exists():
            print('Failed (bundle does not exist); for debugging:',file=sys.stderr)
            print(f'pinliner output:\nstatus code:{repr(pinliner_subbundle.returncode)},stderr:\n{repr(pinliner_subbundle.stderr)}\nstdout:\n{repr(pinliner_subbundle.stdout)}\n',file=sys.stderr)
        assert output_subbundle.exists(), "Error: bundle was not created"
        print('Verify bundle includes key fingerprint...')
        with open(output_subbundle,'r',encoding='utf-8') as f:
            txt = f.read()
            assert 'inliner_packages =' in txt, 'Error: bundle does include the fingerprint'
        print('Patching the bundle...')
        with open(output_subbundle,'a',encoding='utf-8') as f:
            f.write('from src import launcher\n')
        print('done')

    # Step 2. Build the bundle
    print('Calling pinliner...')
    print('Verify bundle exists (it should not)...')
    assert not output_bundle.exists(), f'Failed (bundle already exists before calling pinliner ({output_bundle})'
    args = [python_executable, pinliner_executable, "src", "-o", output_bundle]+pinliner_added_args
    print(f'calling pinliner with the following args: {repr(args)}')
    pinliner_result = subprocess.run(
        args,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert pinliner_result.returncode == 0, f'Failed:\nreturncode == {repr(pinliner_result.returncode)},\n=== STDERR ===\n{pinliner_result.stderr}\n=== END OF STDERR ===\n=== STDOUT ===\n{pinliner_result.stdout}\n=== END OF STDOUT ===\n'
    print('Verify bundle exists...')
    if not output_bundle.exists():
        print('Failed (bundle does not exist); for debugging:',file=sys.stderr)
        print(f'pinliner output:\nstatus code:{repr(pinliner_result.returncode)},stderr:\n{repr(pinliner_result.stderr)}\nstdout:\n{repr(pinliner_result.stdout)}\n',file=sys.stderr)
    assert output_bundle.exists(), "Error: bundle was not created"
    print('Verify bundle includes key fingerprint...')
    with open(output_bundle,'r',encoding='utf-8') as f:
        txt = f.read()
        assert 'inliner_packages =' in txt, 'Error: bundle does include the fingerprint'
    print('Patching the bundle...')
    with open(output_bundle,'a',encoding='utf-8') as f:
        f.write('from src import launcher\nlauncher.main()\n')
    print('done')

    # Step 3. Remove the test program src files, to clearly test the bundle is working without the test files
    print('As bundle exists, remove the src files...')
    shutil.rmtree(tmp_path / 'src')
    print('done')

    # Step 4. Actually, launch the bundle and run the test
    print('starting test...')
    print(f'to verify: bundle is {output_bundle}')
    result = subprocess.run(
        [python_executable, output_bundle, "--program", program_to_test],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f'Failed:\nreturncode == {repr(result.returncode)},\n=== STDERR ===\n{result.stderr}\n=== END OF STDERR ===\n=== STDOUT ===\n{result.stdout}\n=== END OF STDOUT ===\n'
    assert not result.stderr
    for t in [t[1] for t in verify_result_tests if t[0]==program_to_test]:
        t(result.stdout)
    print(f'=== OUTPUT ===\n{result.stdout}\n=== END OF OUTPUT ===\n')
    print("PASS")



def test_pinliner_escape_notspecified_hello(tmp_path):
    return tst(tmp_path,pinliner_added_args=[],program_to_test='test')

def test_pinliner_escape_notspecified_module2(tmp_path):
    return tst(tmp_path,pinliner_added_args=[],program_to_test='module2')

def test_pinliner_escape_notspecified_module3(tmp_path):
    return tst(tmp_path,pinliner_added_args=[],program_to_test='module3')

@pytest.mark.xfail(reason="Recursive inclusion can\'t work, even theoretically. We are loading code from source file but the file does not exist")
def test_pinliner_escape_notspecified_recursive(tmp_path):
    return tst(tmp_path,pinliner_added_args=[],program_to_test='recursive')


def test_pinliner_escape_repr_hello(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','repr'],program_to_test='test')

def test_pinliner_escape_repr_module2(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','repr'],program_to_test='module2')

def test_pinliner_escape_repr_module3(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','repr'],program_to_test='module3')

@pytest.mark.xfail(reason="Recursive inclusion can\'t work, even theoretically. We are loading code from source file but the file does not exist")
def test_pinliner_escape_repr_recursive(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','repr'],program_to_test='recursive')


def test_pinliner_escape_default_quotes_escape_hello(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','default_quotes_escape'],program_to_test='test')

def test_pinliner_escape_default_quotes_escape_module2(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','default_quotes_escape'],program_to_test='module2')

def test_pinliner_escape_default_quotes_escape_module3(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','default_quotes_escape'],program_to_test='module3')

@pytest.mark.xfail(reason="Recursive inclusion can\'t work, even theoretically. We are loading code from source file but the file does not exist")
def test_pinliner_escape_default_quotes_escape_recursive(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','default_quotes_escape'],program_to_test='recursive')


@pytest.mark.xfail(reason="Escaping is normal, it is expected that tests fail if escaping is skipped")
def test_pinliner_escape_skip_hello(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','skip'],program_to_test='test')

@pytest.mark.xfail(reason="Escaping is normal, it is expected that tests fail if escaping is skipped")
def test_pinliner_escape_skip_module2(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','skip'],program_to_test='module2')

@pytest.mark.xfail(reason="Escaping is normal, it is expected that tests fail if escaping is skipped")
def test_pinliner_escape_skip_module3(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','skip'],program_to_test='module3')

@pytest.mark.xfail(reason="Recursive inclusion can\'t work, even theoretically. We are loading code from source file but the file does not exist")
@pytest.mark.xfail(reason="Escaping is normal, it is expected that tests fail if escaping is skipped")
def test_pinliner_escape_skip_recursive(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','skip'],program_to_test='recursive')


def test_pinliner_escape_base64_hello(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','base64'],program_to_test='test')

def test_pinliner_escape_base64_module2(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','base64'],program_to_test='module2')

def test_pinliner_escape_base64_module3(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','base64'],program_to_test='module3')

@pytest.mark.xfail(reason="Recursive inclusion can\'t work, even theoretically. We are loading code from source file but the file does not exist")
def test_pinliner_escape_base64_recursive(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','base64'],program_to_test='recursive')


def test_pinliner_escape_base85_hello(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','base85'],program_to_test='test')

def test_pinliner_escape_base85_module2(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','base85'],program_to_test='module2')

def test_pinliner_escape_base85_module3(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','base85'],program_to_test='module3')

@pytest.mark.xfail(reason="Recursive inclusion can\'t work, even theoretically. We are loading code from source file but the file does not exist")
def test_pinliner_escape_base85_recursive(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','base85'],program_to_test='recursive')


def test_pinliner_escape_zlibbase64_hello(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','zlibbase64'],program_to_test='test')

def test_pinliner_escape_zlibbase64_module2(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','zlibbase64'],program_to_test='module2')

def test_pinliner_escape_zlibbase64_module3(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','zlibbase64'],program_to_test='module3')

@pytest.mark.xfail(reason="Recursive inclusion can\'t work, even theoretically. We are loading code from source file but the file does not exist")
def test_pinliner_escape_zlibbase64_recursive(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','zlibbase64'],program_to_test='recursive')


def test_pinliner_escape_zlibbase85_hello(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','zlibbase85'],program_to_test='test')

def test_pinliner_escape_zlibbase85_module2(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','zlibbase85'],program_to_test='module2')

def test_pinliner_escape_zlibbase85_module3(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','zlibbase85'],program_to_test='module3')

@pytest.mark.xfail(reason="Recursive inclusion can\'t work, even theoretically. We are loading code from source file but the file does not exist")
def test_pinliner_escape_zlibbase85_recursive(tmp_path):
    return tst(tmp_path,pinliner_added_args=['--embed-code-encoding','zlibbase85'],program_to_test='recursive')
