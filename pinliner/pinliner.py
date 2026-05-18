#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

import argparse
import json
import os
import sys
std_import_error = None
try:
    import base64
    import zlib
except ImportError as e:
    std_import_error = e # to make it optional
try:
    from pinliner import __version__
except ImportError:
    # from ..pinliner import __version__
    # aaah ugly hack sorry
    # this is called if we don't have pinliner installed as a module - if we simply grab it from gsource codes
    # so we can still use it
    # AP 11/12/2024
    _i = os.path.dirname(os.path.abspath(__file__+'/..'))
    sys.path.insert(0,_i)
    from pinliner import __version__
    #__version__ = '0.2.0'
import re



TEMPLATE_FILE = 'importer.template'
TEMPLATE_PATTERN = '${CONTENTS}'


# class UnsupportedEncodingError(NotImplementedError):
#     """Requested encoding is not implemented by pinliner."""
class UnsupportedEncodingError(ValueError): # chatgpt insists it should be derived from Value Error, but I think using NotImplementedError is reasonable... Anyway, I should account for future users and maintainers, and I'll use more conventional, proposed by chatgpt, ValueError
    """Requested encoding is not implemented by pinliner."""

def encode_payload(code,payload_encoding):
    if not payload_encoding:
        payload_encoding = 'repr'
    # choices = ['repr','default_quotes_escape','skip','base64','base85','zlibbase64','zlibbase85'],
    if payload_encoding=='skip':
        triquo_start = "r'''\\n"
        triquo_end = "\\n'''"
        return triquo_start + code + triquo_end
    elif payload_encoding=='repr':
        return f'{code!r}'
    elif payload_encoding=='default_quotes_escape':
        triquo_start = "'''\\n"
        triquo_end = "\\n'''"
        return triquo_start + re.sub(r'(\'{3})',lambda m: f'\\\'\\\'\\\'', code) + triquo_end
    elif payload_encoding=='base64':
        if not base64 and std_import_error:
            raise std_import_error
        return '"'+base64.b64encode(code.encode("utf-8")).decode("ascii")+'"'
    elif payload_encoding=='zlibbase64':
        if (not base64 or not zlib) and std_import_error:
            raise std_import_error
        code_raw = code.encode("utf-8")
        code_compressed = zlib.compress(code_raw, level=9)
        return '"'+base64.b64encode(code_compressed).decode("ascii")+'"'
    elif payload_encoding=='base85':
        if not base64 and std_import_error:
            raise std_import_error
        return '"'+base64.b85encode(code.encode("utf-8")).decode("ascii")+'"'
    elif payload_encoding=='zlibbase85':
        if (not base64 or not zlib) and std_import_error:
            raise std_import_error
        code_raw = code.encode("utf-8")
        code_compressed = zlib.compress(code_raw, level=9)
        return '"'+base64.b85encode(code_compressed).decode("ascii")+'"'
    else:
        raise UnsupportedEncodingError('pinliner: encoding payload with method == "{m}": not implemented'.format(m=payload_encoding))

def decode_payload(code,payload_encoding):
    if not payload_encoding:
        payload_encoding = 'repr'
    # choices = ['repr','default_quotes_escape','skip','base64','base85','zlibbase64','zlibbase85'],
    if payload_encoding=='skip':
        triquo_start = "r'''\\n"
        triquo_end = "\\n'''"
        assert code.startswith(triquo_start) and code.endswith(triquo_end), 'pinliner: encoding with "skip" - sring must be wrapped with triple quotes'
        return code[len(triquo_start):-len(triquo_end)]
    elif payload_encoding=='repr':
        return eval(code)
    elif payload_encoding=='default_quotes_escape':
        triquo_start = "'''\\n"
        triquo_end = "\\n'''"
        assert code.startswith(triquo_start) and code.endswith(triquo_end), 'pinliner: encoding with "skip" - sring must be wrapped with triple quotes'
        code = code[len(triquo_start):-len(triquo_end)]
        code = re.sub(r'\\\'\\\'\\\'',lambda m: "'''", code)
        return code
    elif payload_encoding=='base64':
        if not base64 and std_import_error:
            raise std_import_error
        return base64.b64decode(code[1:-1].encode("ascii")).decode("utf-8")
    elif payload_encoding=='zlibbase64':
        if (not base64 or not zlib) and std_import_error:
            raise std_import_error
        code_compressed = base64.b64decode(code[1:-1].encode("ascii"))
        code_raw = zlib.decompress(code_compressed)
        return code_raw.decode("utf-8")
    elif payload_encoding=='base85':
        if not base64 and std_import_error:
            raise std_import_error
        return base64.b85decode(code[1:-1].encode("ascii")).decode("utf-8")
    elif payload_encoding=='zlibbase85':
        if (not base64 or not zlib) and std_import_error:
            raise std_import_error
        code_compressed = base64.b85decode(code[1:-1].encode("ascii"))
        code_raw = zlib.decompress(code_compressed)
        return code_raw.decode("utf-8")
    else:
        raise UnsupportedEncodingError('pinliner: encoding payload with method == "{m}": not implemented'.format(m=payload_encoding))



def output(cfg, what, newline=True):
    # We need indentation for PEP8
    cfg.outfile.write(what)
    if newline:
        cfg.outfile.write(os.linesep)


def process_file(cfg, base_dir, package_path):
    try:
        if cfg.tagging:
            output(cfg, '<tag:' + package_path + '>')
        path = os.path.splitext(package_path)[0].replace(os.path.sep, '.')
        package_start = cfg.outfile.tell()
        full_path = os.path.join(base_dir, package_path)
        with open(full_path, 'r',encoding='utf-8') as f:
            # Read the whole file
            code = f.read()

            # Insert escape character before ''' since we'll be using ''' to insert
            # the code as a string
            # code = code.replace("'''", r"\'''")
            code = encode_payload(code,cfg.payload_encoding)
            output(cfg, code+"\n", newline=cfg.tagging)
        package_end = package_start + len(code)
        is_package = 1 if path.endswith('__init__') else 0
        if is_package:
            path = path[:-9]

        # Get file timestamp
        timestamp = int(os.path.getmtime(full_path))
        return path, is_package, package_start, package_end, timestamp
    except Exception as e:
        print('pinliner: failed when processing package {f}'.format(f=package_path))
        raise e


def template(cfg):
    template_path = os.path.join(os.path.dirname(__file__), TEMPLATE_FILE)
    with open(template_path) as f:
        template = f.read()
    prefix_end = template.index(TEMPLATE_PATTERN)
    prefix_data = template[:prefix_end].replace('%{FORCE_EXC_HOOK}',
                                                str(cfg.set_hook))
    prefix_data = prefix_data.replace('%{DEFAULT_PACKAGE}', cfg.default_package).replace('%{CONFIG_VERBOSE}','True' if cfg.verbose else 'False').replace('%{CONFIG_PAYLOAD_ENCODING}','\''+cfg.payload_encoding+'\'')
    cfg.outfile.write(prefix_data)
    postfix_begin = prefix_end + len(TEMPLATE_PATTERN)
    return template[postfix_begin:].replace('%{CONFIG_VERBOSE}','True' if cfg.verbose else 'False').replace('%{CONFIG_PAYLOAD_ENCODING}','\''+cfg.payload_encoding+'\'')


def process_directory(cfg, base_dir, package_path):
    try:
        files = []
        contents = os.listdir(os.path.join(base_dir, package_path))
        for content in contents:
            next_path = os.path.join(package_path, content)
            path = os.path.join(base_dir, next_path)
            if is_module(path):
                files.append(process_file(cfg, base_dir, next_path))
            elif is_package(path):
                files.extend(process_directory(cfg, base_dir, next_path))
        return files
    except Exception as e:
        print('pinliner: failed when processing package {f}'.format(f=package_path))
        raise e


def process_files(cfg):
    # template would look better as a context manager
    postfix = template(cfg)
    files = []
    # output(cfg, "r'''")
    for package_path in cfg.packages:
        base_dir, module_name = os.path.split(package_path)
        files.extend(process_directory(cfg, base_dir, module_name))
    # output(cfg, "'''")

    # Transform the list into a dictionary
    inliner_packages = {data[0]: data[1:] for data in files}

    # Generate the references to the positions of the different packages and
    # modules inside the main file.
    # We don't use indent to decrease the number of bytes in the file
    data = json.dumps(inliner_packages)
    output(cfg, 2 * os.linesep + 'inliner_packages = ', newline=False)
    data = data.replace('],', '],' + os.linesep + '   ')
    data = data.replace('[', '[' + os.linesep + 8 * ' ')
    data = '%s%s    %s%s%s' % (data[0], os.linesep, data[1:-1], os.linesep,
                               data[-1])

    output(cfg, data)
    # No newline on last line, as we want output file to be PEP8 compliant.
    output(cfg, postfix, newline=False)
    cfg.outfile.close()


def parse_args():
    class MyParser(argparse.ArgumentParser):
        """Class to print verbose help on error."""
        def error(self, message):
            self.print_help()
            sys.stderr.write('\nERROR: %s\n' % message)
            sys.exit(2)

    general_description = """Pinliner - Python Inliner (Version %s)

    This tool allows you to merge all files that comprise a Python package into
a single file and be able to use this single file as if it were a package.

    Imports will work as usual so if you have a package structure like:
        .
        └── [my_package]
             ├── file_a.py
             ├── [sub_package]
             │    ├── file_b.py
             │    └── __init__.py
             ├── __init__.py

    And you execute:
        $ mkdir test
        $ pinliner my_package test/my_package.py
        $ cd test
        $ python

    You'll be able to use this file as if it were the real package:
        >>> import my_package
        >>> from my_package import file_a as a_file
        >>> from my_package.sub_package import file_b

    And __init__.py contents will be executed as expected when importing
my_package and you'll be able to access its contents like you would with your
normal package.  Modules will also behave as usual.

    By default there is no visible separation between the different modules'
source code, but one can be enabled for clarity with option --tag, which will
include a newline and a <tag:file_path> tag before each of the source files.
""" % __version__
    general_epilog = None

    parser = MyParser(description=general_description,
                      epilog=general_epilog, argument_default='',
                      formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('packages', nargs='+', help='Packages to inline.')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('-o', '--outfile', nargs='?',
                        type=argparse.FileType('w',encoding='utf-8'),
                        default=sys.stdout, help='Output file.')
    parser.add_argument('--set-except', default=None, dest='set_hook',
                        action='store_true',
                        help='Force setting handler for uncaught exceptions.')
    parser.add_argument('--no-except', default=None, dest='set_hook',
                        action='store_false',
                        help="Don't set handler for uncaught exceptions.")
    parser.add_argument('--tag', default=False, dest='tagging',
                        action='store_true',
                        help="Mark with <tag:file_path> each added file.")
    parser.add_argument('--verbose', default=False, dest='verbose',
                        action='store_true',
                        help="Print messages about modules being loaded and .py module files with code along with .pyc for debugging (warning: lots of messages, only for debugging)")
    parser.add_argument('--embed-code-encoding', dest='payload_encoding',
                        type = str,
                        choices = ['repr','default_quotes_escape','skip','base64','base85','zlibbase64','zlibbase85'],
                        default='repr',
                        help="Control the encoding method for payload (embedded code), possible values are \"default_quotes_escape\" (should be safe escaping but I am not 100% sure), \"skip\" (no transformation, will possibly break if embedded code contains triple quotes), \"base64\" (all encoded with base64, that solves all problems with quotes escaping, the code looks obfuscated but still not a problem for LLMs to analyze, bundle size gets 30% bigger), \"base85\" (same as base64 but with longer dictionary and is more efficient), \"zlibbase64\" (same as base64 but passed through compression to reduce file size), \"zlibbase85\" (same as zlibbase64 but more space-efficient)")
    parser.add_argument('-d', '--default-pkg', default=None,
                        dest='default_package',
                        help='Define the default package when multiple '
                             'packages are inlined.')
    cfg = parser.parse_args()
    # If user didn't pass a default package determine one ourselves.
    if cfg.default_package is None:
        # For single package file default is the package, for multiple packaged
        # files default is none (act as a bundle).
        def_file = cfg.packages[0] if len(cfg.packages) == 1 else ''
        cfg.default_package = def_file
    return cfg


def is_module(module):
    # This validation is poor, but good enough for now
    return os.path.isfile(module) and module.endswith('.py')


def is_package(package):
    init_file = os.path.join(package, '__init__.py')
    return os.path.isdir(package) and os.path.isfile(init_file)


def validate_args(cfg):
    missing = False
    # This is weird now, but in the future we'll allow to inline multiple
    # packages
    for package in cfg.packages:
        if not is_package(package):
            sys.stderr.write('ERROR: %s is not a python package' % package)
            missing = True
    if missing:
        sys.exit(1)

    if cfg.default_package:
        if cfg.default_package not in cfg.packages:
            sys.stderr.write('ERROR: %s is not a valid default package, valid are only: [ %s ]' %
                             ( cfg.default_package, ', '.join(list(cfg.packages)) ))
            sys.exit(2)
        # Convert the default package from path to package
        cfg.default_package = os.path.split(cfg.default_package)[1]


def main():
    cfg = parse_args()
    validate_args(cfg)
    process_files(cfg)


if __name__ == '__main__':
    main()
