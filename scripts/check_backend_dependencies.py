from myUtils.backend_runtime import REQUIRED_BACKEND_MODULES, find_missing_backend_modules


def main() -> int:
    """检查后端关键依赖是否完整，缺失时输出模块名并返回非零状态。"""
    missing_modules = find_missing_backend_modules(REQUIRED_BACKEND_MODULES)
    if not missing_modules:
        print("OK")
        return 0

    print("MISSING:" + ",".join(missing_modules))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
