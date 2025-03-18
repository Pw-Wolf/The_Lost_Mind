import os
import shutil
import subprocess
import sys
from decimal import Decimal

sys.dont_write_bytecode = True

mypath = os.getcwd()


def make_build() -> None:
    if not os.path.exists(mypath + "\\build"):
        os.makedirs(mypath + "\\build")
    if not os.path.exists(mypath + "\\builds"):
        os.makedirs(mypath + "\\builds")


def move_to_build() -> None:
    onlyfiles = [f for f in os.listdir(mypath) if os.path.isfile(os.path.join(mypath, f))]
    for name in [".\\components\\", ".\\core\\", ".\\game\\", ".\\updates\\"]:
        mypath_comp = mypath + name
        onlyfiles += [name + f for f in os.listdir(mypath_comp) if os.path.isfile(os.path.join(mypath_comp, f))]

    print("\n"*2)
    for i in onlyfiles:
        if i[-3:] == ".py" and i not in ("updates\\make_exe.py", "zz.py", "testiranje_api.py", "test.py", "current_lines.py"):

            print(f"{'*'*10} {i}")

            with open(i, 'r') as o:
                output = o.read()

            clean = output.replace("components.", "")
            for component in ["\\components\\", "\\core\\", "game\\", "updates\\"]:
                i = i.replace(component, "")

            if not os.path.exists(f"build\\{i}"):
                with open(f"build\\{i}", 'w') as o:
                    o.write(clean)


def clean_after_compile() -> None:
    build_path = mypath + "\\build"
    build_files = ["build\\" + f for f in os.listdir(build_path) if os.path.isfile(os.path.join(build_path, f))]

    for myfile in build_files:
        if os.path.exists(myfile):
            os.remove(myfile)


def compile_to_exe():
    cwd = fr"{mypath}\\build"
    icon = fr"{mypath}/assets/images/icon.ico"
    py_file = fr"{mypath}\main.py"

    upx_location = r'"C:\Program Files\upx-4.2.4-win64"'
    subprocess.call(fr'python -m PyInstaller --clean --noconsole --onefile --icon {icon} --name The_Lost_Mind --upx-dir {upx_location} {py_file}', cwd=cwd)


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        source = os.path.join(src, item)
        destination = os.path.join(dst, item)
        if os.path.isdir(source):
            shutil.copytree(source, destination, symlinks, ignore)
            return
        shutil.copy2(source, destination)


def making_package_for_exe(version) -> None:
    # Moving the executable
    exe_path = f"{mypath}\\build\\dist\\The_Lost_Mind.exe"
    new_exe_path = f"{mypath}\\builds\\The_Lost_Mind_{version}"
    if not os.path.exists(new_exe_path):
        os.makedirs(new_exe_path)

    if not os.path.exists(new_exe_path + "\\assets"):
        os.makedirs(new_exe_path + "\\assets")

    print(new_exe_path + f"\\The_Lost_Mind.exe")
    print(exe_path)
    os.rename(exe_path, new_exe_path + f"\\The_Lost_Mind.exe")

    # moving needed files for executable to run
    data_path = f"{mypath}\\assets"
    copytree(data_path, new_exe_path + "\\assets")


def increase_game_version():
    with open("updates/constant.py", "w") as o:
        new_version = float(Decimal(str(version)) + Decimal('0.1'))
        new = f'VERSION = {new_version}'
        o.write(new)


def maniupulation_exe():
    py_file = fr"{mypath}\\updates\\manipulation.py"
    new_exe_path = f"{mypath}\\builds\\The_Lost_Mind_{version}"
    data_path = f"{mypath}\\builds\\The_Lost_Mind_{version}\\data"
    subprocess.call(fr"python -m PyInstaller --clean --noconsole --onefile --name manipulation {py_file}", cwd=data_path)


if __name__ == "__main__":
    make_build()
    move_to_build()

    from constant import VERSION
    version = VERSION

    compile_to_exe()
    making_package_for_exe(version)
    clean_after_compile()
    increase_game_version()
