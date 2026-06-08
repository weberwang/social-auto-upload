from importlib.util import find_spec

REQUIRED_BACKEND_MODULES = (
    "flask",
    "flask_cors",
    "click",
    "werkzeug",
    "jinja2",
    "blinker",
    "itsdangerous",
    "segno",
    "playwright",
    "patchright",
    "xhs",
    "loguru",
    "cv2",
)


def find_missing_backend_modules(module_names: list[str] | tuple[str, ...]) -> list[str]:
    """返回缺失的后端运行时模块列表，供启动脚本决定是否自动补装依赖。"""
    missing_modules: list[str] = []

    for module_name in module_names:
        if find_spec(module_name) is None:
            missing_modules.append(module_name)

    return missing_modules
