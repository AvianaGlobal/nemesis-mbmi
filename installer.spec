# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

pathex = [
    '%HOMEPATH%/install_test/mbmi'
]

binaries= [
    ('venv27_win/library/bin/*.dll', '.'),
    ('venv27_win/Lib/site-packages/PyQt4/*.dll', '.'),
    ('C:/Program Files (x86)/Windows Kits/10/Redist/10.0.18362.0/ucrt/DLLs/x64/*.dll', '.'),
]

datas = [
    ('nemesis/app/builder/*.enaml', 'nemesis/app/builder/'),
    ('nemesis/app/common/*.enaml', 'nemesis/app/common/'),
    ('nemesis/app/inspector/*.enaml', 'nemesis/app/inspector/'),
    ('nemesis/data/ui/*.enaml', 'nemesis/data/ui/'),
    ('nemesis/r/ui/*.enaml', 'nemesis/r/ui/'),
    ('nemesis/stdlib/ui/*.enaml', 'nemesis/stdlib/ui/'),
    ('nemesis/ui/*.enaml', 'nemesis/ui/'),
    ('nemesis/app/common/images/*.png', 'nemesis/app/common/images/'),
    ('nemesis/app/common/images/*.jpg', 'nemesis/app/common/images/'),
]

hiddenimports = [
    'backports',
    'cython',
    'enaml',
    'qtpy',
    'rpy2',
    'pyface.toolkits',
    'pyodbc',
    'PyQt4',
    'pywin32',
    'pyzmq',
    'pkg_resources.py2_warn',
    'matplotlib',
    'multiprocessing',
    'traitlets',
    'traits',
    'traitsui',
    'wxpython',
]

excludes = [
    'FixTk',
    'tcl',
    'tk',
    '_tkinter',
    'tkinter',
    'Tkinter',
]

a = Analysis(['nemesis/app/builder/main.py'],
             pathex=pathex,
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             excludes=excludes,
             win_no_prefer_redirects=True,
             win_private_assemblies=True,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='ModelBuilder',
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               upx_exclude=[],
               name='ModelBuilder')
