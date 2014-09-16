# -*- mode: python -*-
a = Analysis(['io_server.py'],
             pathex=['/Users/jmrbcu/Development/smart_kiosk'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='card_reader',
          debug=False,
          strip=True,
          upx=True,
          console=True )
