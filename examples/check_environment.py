# -*- coding: utf-8 -*-
"""Pre-flight check for the ENVI Automation Skill worked example.

Run: python examples/check_environment.py
No ENVI licence is used and nothing is executed — it only checks
that ENVI can be found, paths are pure ASCII, and .pro files use CRLF.
"""
import glob
import os
import pathlib


def find_envi():
    cands = [
        r'C:\Program Files\NV5\ENVI62\IDL92\bin\bin.x86_64\idl.exe',
        r'C:\Program Files\Harris\ENVI56\IDL88\bin\bin.x86_64\idl.exe',
    ]
    for pat in [r'C:\Program Files\NV5\ENVI*\IDL*\bin\bin.x86_64\idl.exe',
                r'C:\Program Files\Harris\ENVI*\IDL*\bin\bin.x86_64\idl.exe']:
        cands += glob.glob(pat)
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


def main():
    idl = find_envi()
    print('ENVI/IDL:', idl or 'NOT FOUND')
    print('IDL_LICENSE_PATH:', os.environ.get('IDL_LICENSE_PATH', '(not set)'))
    root = pathlib.Path(__file__).resolve().parents[1]
    problems = []
    for p in sorted(root.rglob('*.pro')):
        data = p.read_bytes()
        if b'\r\n' not in data:
            problems.append(f'{p.relative_to(root)}: not CRLF')
        try:
            str(p)
            p.as_posix().encode('ascii')
        except UnicodeEncodeError:
            problems.append(f'{p.relative_to(root)}: non-ASCII path')
    print('CRLF / ASCII check:', 'OK' if not problems else problems)
    print('Done. Fix any line above before running the IDL pipeline.')


if __name__ == '__main__':
    main()
