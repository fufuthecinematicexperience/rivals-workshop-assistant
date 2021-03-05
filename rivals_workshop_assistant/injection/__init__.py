from .application import apply_injection
from .dependency_handling import GmlInjection
from .library import read_injection_library


def handle_injection(scripts):
    injection_library = read_injection_library()
    result_scripts = apply_injection(scripts, injection_library)
    return result_scripts
