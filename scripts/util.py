#!/usr/bin/python

import os, sys, subprocess

if os.name == "nt":
    def symlink_ms(source, link_name):
        import ctypes
        csl = ctypes.windll.kernel32.CreateSymbolicLinkW
        csl.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
        csl.restype = ctypes.c_ubyte
        flags = 1 if os.path.isdir(source) else 0
        try:
            if csl(link_name, source.replace('/', '\\'), flags) == 0:
                raise ctypes.WinError()
        except:
            pass
    os.symlink = symlink_ms

# Cache a single cygpath process for use throughout, even across instances of
# the PlatformUtility class.
_cygpath_proc = None

def getAbsolutePath(path, force=False):
    """Returns an absolute windows path. If platform is cygwin, converts it to
    windows style using cygpath.
    For performance reasons, we use a single cygpath process, shared among all
    instances of this class. Otherwise Python can run out of file handles.
    """
    if not force and sys.platform != "cygwin":
      path = os.path.abspath(path)
    global _cygpath_proc
    if not _cygpath_proc:
      cygpath_command = ["cygpath.exe",
                         "-a", "-w", "-f", "-"]
      _cygpath_proc = subprocess.Popen(cygpath_command,
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE)
    _cygpath_proc.stdin.write(path + "\n")
    return _cygpath_proc.stdout.readline().rstrip()

def getCygwinPath(path):
    """Convert a Windows path to a cygwin path.
    The cygpath utility insists on converting paths that it thinks are Cygwin
    root paths to what it thinks the correct roots are.  So paths such as
    "C:\b\slave\webkit-release-kjs\build\third_party\cygwin\bin" are converted to
    plain "/usr/bin".  To avoid this, we do the conversion manually.
    The path is expected to be an absolute path, on any drive.
    """
    if sys.platform != "cygwin":
        return path
    drive_regexp = re.compile(r'([a-z]):[/\\]', re.IGNORECASE)
    def LowerDrive(matchobj):
        return '/cygdrive/%s/' % matchobj.group(1).lower()
    path = drive_regexp.sub(LowerDrive, path)
    return path.replace('\\', '/').replace('//','/')

def backup(fname,maxfile=5,ext='.bak'):
    fbak = fname+ext
    if maxfile>=2:
        for i in xrange(maxfile-2,0,-1):
            if os.path.isfile(fbak+str(i)):
                os.rename(fbak+str(i),fbak+str(i+1))
        if os.path.isfile(fbak):
            os.rename(fbak,fbak+'1')
    os.rename(fname,fbak)

