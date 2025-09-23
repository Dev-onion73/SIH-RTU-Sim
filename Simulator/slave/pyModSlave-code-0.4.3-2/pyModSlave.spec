# -*- mode: python ; coding: utf-8 -*-

# remove all Qt dlls except : Qt5Core, Qt5Gui, Qt5Widgets
# remove PyQt5\Qt\bin folder

block_cipher = None

added_files = [('ManModbus','ManModbus')]

a = Analysis(['pyModSlave.py'],
             pathex=['C:\\Projects\\python\\pyModSlave'],
             binaries=[],
             datas=added_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='pyModSlave',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
		  icon='C:\\Projects\\python\\pyModSlave\\ui\\icons\Bus.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='pyModSlave')
