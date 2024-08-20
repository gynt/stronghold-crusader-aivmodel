import ctypes
import os

from pymem import Pymem

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


process_id = create_suspended_process()

from pymem import Pymem
import os
process = Pymem(process_id)
process.inject_python_interpreter()
filepath = os.path.abspath('.')
filepath = filepath.replace("\\", "\\\\")
shellcode = """

import sys
sys.path.insert(0, "{0}")

import aivmodel
aivmodel.main({1})



""".format(filepath, process_id)
process.inject_python_shellcode(shellcode)

