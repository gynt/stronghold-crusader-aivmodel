import ctypes
import os

from pymem import Pymem

import argparse
import pathlib

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument('handler')
arg_parser.add_argument('-v', '--verbose', action='store_true')
args = arg_parser.parse_args()

path = pathlib.Path(args.handler).absolute()
if path.is_dir():
    raise NotImplementedError()

sys_path_append = str(path.parent)
main_file = str(path.stem)

if args.verbose:
    print(f"handler: file: {main_file} folder: {sys_path_append}")

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)


class STARTUPINFO(ctypes.Structure):
    _fields_ = [
        ('cb', ctypes.c_uint32),
        ('lpReserved', ctypes.c_char_p),
        ('lpDesktop', ctypes.c_char_p),
        ('lpTitle', ctypes.c_char_p),
        ('dwX', ctypes.c_uint32),
        ('dwY', ctypes.c_uint32),
        ('dwXSize', ctypes.c_uint32),
        ('dwYSize', ctypes.c_uint32),
        ('dwXCountChars', ctypes.c_uint32),
        ('dwYCountChars', ctypes.c_uint32),
        ('dwFillAttribute', ctypes.c_uint32),
        ('dwFlags', ctypes.c_uint32),
        ('wShowWindow', ctypes.c_uint16),
        ('cbReserved2', ctypes.c_uint16),
        ('lpReserved2', ctypes.c_char_p),
        ('hStdInput', ctypes.c_void_p),
        ('hStdOutput', ctypes.c_void_p),
        ('hStdError', ctypes.c_void_p),
    ]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ('hProcess', ctypes.c_void_p),
        ('hThread', ctypes.c_void_p),
        ('dwProcessId', ctypes.c_uint32),
        ('dwThreadId', ctypes.c_uint32),
    ]


def create_suspended_process():
    startupInfo = STARTUPINFO()
    processInformation = PROCESS_INFORMATION()
        
    kernel32.CreateProcessA(
        None,
        (r'"C:\Program Files (x86)\Steam\steamapps\common\Stronghold Crusader Extreme\Stronghold Crusader.exe"').encode(),
        None,
        None,
        False,
        # Create the process suspended
        ctypes.c_uint32(0x00000000),
        None,
        "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Stronghold Crusader Extreme\\".encode(),
        ctypes.byref(startupInfo),
        ctypes.byref(processInformation)
    )
    
    return processInformation.dwProcessId


from pymem import Pymem
import os
if args.verbose:
    print("attaching to process")

try:
  process = Pymem("Stronghold Crusader")
  process_id = process.process_id
except:
  process_id = create_suspended_process()
  process = Pymem(process_id)

if args.verbose:
    print("injecting python interpreter")
process.inject_python_interpreter()
filepath = os.path.abspath('.')
filepath = filepath.replace("\\", "\\\\")
shellcode = """

import win32api, win32con

win32api.MessageBox(None, f"Hello!", "Test", win32con.MB_OKCANCEL)

log = open('aivmodel.log', 'w')

import sys
sys.path.insert(0, "{0}")
sys.path.insert(0, "{1}")

import aivmodel

# To register a handler
from {2} import HANDLER
print("setting handler: {{HANDLER}}")
# aivmodel.set_handler(HANDLER)

# Never returns
print("running main", file = log)
try:
  aivmodel.main({3}, HANDLER)
except Exception as e:
  print(f"error: {{e}}", file = log)
print("exiting...", file = log)

""".format(filepath, sys_path_append, main_file, process_id)
if args.verbose:
    print("injecting python shellcode")
process.inject_python_shellcode(shellcode)
if args.verbose:
    print("exiting")
