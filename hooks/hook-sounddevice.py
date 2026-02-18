from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

hiddenimports = ["_sounddevice_data"]
datas = collect_data_files("sounddevice") + collect_data_files("_sounddevice_data")
binaries = collect_dynamic_libs("_sounddevice_data")
