import pathlib, sys


def icon_root():
    """
    Get the absolute path to a resource.
    Works seamlessly during local development and inside the PyInstaller .exe
    """
    if hasattr(sys, '_MEIPASS'):
        # Inside the .exe, files are extracted to a temporary folder (sys._MEIPASS)
        return pathlib.Path(sys._MEIPASS) / "icons"
    else:
        # Outside the .exe (local dev), look relative to where THIS script is located
        # Change ".." if your icons folder is located somewhere else relative to this script
        return (pathlib.Path(__file__).parent.parent / "icons").resolve().relative_to(
            pathlib.Path.cwd(), walk_up=True)

def gtk_root():
    """
    Get the absolute path to a resource.
    Works seamlessly during local development and inside the PyInstaller .exe
    """
    if hasattr(sys, '_MEIPASS'):
        # Inside the .exe, files are extracted to a temporary folder (sys._MEIPASS)
        return pathlib.Path(sys._MEIPASS) / "GTK3-Runtime Win64"
    else:
        # Outside the .exe (local dev), look relative to where THIS script is located
        # Change ".." if your icons folder is located somewhere else relative to this script
        return (pathlib.Path(__file__).parent.parent / "lib" / "GTK3-Runtime Win64").resolve() # .relative_to(
            #pathlib.Path.cwd(), walk_up=True)
