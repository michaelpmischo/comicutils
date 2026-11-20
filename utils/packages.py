import importlib, sys, subprocess, typing


def _install_package(package_in):
    print(f"Installing: {package_in}...")
    subprocess.run(
        [f"{sys.executable}", "-m", "pip", "install", package_in, "--break-system-packages"],
        stderr=subprocess.STDOUT,
        text=True)


def _uninstall_package(package_in):
    print(f"Uninstalling: {package_in}...")
    subprocess.run(
        [f"{sys.executable}", "-m", "pip", "uninstall", "-y", package_in, "--break-system-packages"],
        stderr=subprocess.STDOUT,
        text=True)


def _ensure_pip_update() -> bool:
    print(f"Updating pip...")
    subprocess.run(
        [f"{sys.executable}", "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
        stderr=subprocess.STDOUT,
        text=True)


def _ensure_package(imp_in: str, pkg_in: str) -> bool:
    """Internal helper to verify/install packages."""
    # Check top-level package or explicit sub-module path
    try:
        importlib.import_module(imp_in)
        return True
    except (ImportError, ModuleNotFoundError, OSError) as _:
        print(f"📦 [packages] {imp_in} missing. Installing: {pkg_in}...")
        try:
            _ensure_pip_update()
            _install_package(pkg_in)
            return True
        except subprocess.CalledProcessError:
            print(f"❌ [packages] Failed to install {pkg_in}.")
            return False


def require(dependencies_in: typing.Dict[str, typing.Tuple[str, str]], module_in: str) -> None:
    """
    Installs and dynamically binds dependencies to a target module's scope.

    Args:
        dependencies: A dict of {"Variable_Name": ("Import_Path", "PyPI_Name")}
        target_module_name: The __name__ of the module calling this function.
    """
    # Grab the actual module object of the file calling this function
    module = sys.modules[module_in]

    # Initialize __all__ if the caller doesn't have it defined yet
    if not hasattr(module, "__all__"):
        module.__all__ = []

    for name_in, (imp, pkg) in dependencies_in.items():
        if _ensure_package(imp, pkg):
            try:
                # Dynamically import the target module or sub-attribute
                package = importlib.import_module(imp)

                # Bind it to the caller's global namespace
                setattr(module, name_in, package)

                # Append to caller's __all__ list
                if name_in not in module.__all__:
                    module.__all__.append(name_in)

            except ImportError as error:
                print(f"⚠️ [packages] Imported but failed to bind {name_in}: {error}")
                setattr(module, name_in, None)
        else:
            setattr(module, name_in, None)
