from pathlib import Path
import sys


def _ensure_project_root_on_sys_path() -> None:
    """确保脚本按文件路径直接运行时也能导入项目根目录下的包。"""

    project_root = Path(__file__).resolve().parents[1]
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        # 预检脚本经常由 bat 以绝对路径直接调用，这时 sys.path[0] 会落在 scripts 目录。
        sys.path.insert(0, project_root_str)


def _load_backend_runtime():
    """延迟导入后端运行时探测模块，避免入口在导入阶段直接崩溃。"""

    _ensure_project_root_on_sys_path()
    from myUtils.backend_runtime import (  # pylint: disable=import-outside-toplevel
        REQUIRED_BACKEND_MODULES,
        find_missing_backend_modules,
    )

    return REQUIRED_BACKEND_MODULES, find_missing_backend_modules


def main() -> int:
    """检查后端关键依赖是否完整，缺失时输出模块名并返回非零状态。"""

    required_backend_modules, find_missing_backend_modules = _load_backend_runtime()
    missing_modules = find_missing_backend_modules(required_backend_modules)
    if not missing_modules:
        print("OK")
        return 0

    print("MISSING:" + ",".join(missing_modules))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
