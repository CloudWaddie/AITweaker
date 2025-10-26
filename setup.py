from cx_Freeze import setup, Executable

build_options = {'packages': [], 'excludes': [], 'include_files': ['proxy.py']}

base = 'gui'

executables = [
    Executable('gui.py', base=base)
]

setup(name='AITweaker',
      version = '1',
      description = 'A tool to enable new features in AI apps',
      options = {'build_exe': build_options},
      executables = executables)
