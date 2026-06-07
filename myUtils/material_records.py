import sqlite3
from collections.abc import Mapping

MATERIAL_VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv", ".m4v", ".webm", ".flv", ".wmv")
MATERIAL_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
MaterialRecordValue = str | int | float | None


def ensure_file_records_schema(connection: sqlite3.Connection) -> None:
    """确保素材表包含备注字段，避免老数据库因缺列导致上传或查询失败。"""
    cursor = connection.cursor()
    cursor.execute("PRAGMA table_info(file_records)")
    column_names = {row[1] for row in cursor.fetchall()}
    if "remark" not in column_names:
        cursor.execute("ALTER TABLE file_records ADD COLUMN remark TEXT DEFAULT ''")
        connection.commit()


def extract_material_uuid(file_path: str | None) -> str:
    """从素材存储路径中提取 UUID，兼容历史数据缺失或格式异常的情况。"""
    if not file_path:
        return ""

    file_path_parts = file_path.split("_", 1)
    if len(file_path_parts) == 0:
        return ""
    return file_path_parts[0]


def serialize_material_row(row: sqlite3.Row) -> dict[str, MaterialRecordValue]:
    """把 SQLite 行对象转换为前端素材记录，并补齐 UUID 字段。"""
    row_dict = dict(row)
    row_dict["uuid"] = extract_material_uuid(row_dict.get("file_path"))
    return row_dict


def parse_positive_int(value: str | None, default: int) -> int:
    """解析正整数分页参数，非法值统一回退到默认值。"""
    if value is None:
        return default

    try:
        parsed_value = int(value)
    except ValueError:
        return default
    if parsed_value < 1:
        return default
    return parsed_value


def should_use_paginated_material_query(args: Mapping[str, str]) -> bool:
    """判断当前请求是否进入分页查询分支，兼容旧版全量拉取调用。"""
    return any(
        args.get(parameter_name) is not None
        for parameter_name in ("page", "page_size", "keyword", "material_type", "sort_by", "sort_order")
    )


def build_extension_like_clause(extensions: tuple[str, ...]) -> tuple[str, list[str]]:
    """根据扩展名列表构造 SQL LIKE 片段，保证类型过滤与前端口径一致。"""
    clause = " OR ".join("LOWER(filename) LIKE ?" for _ in extensions)
    return f"({clause})", [f"%{extension}" for extension in extensions]


def build_material_filter_clause(keyword: str | None, material_type: str | None) -> tuple[str, list[str]]:
    """构造素材列表过滤条件，支持关键字与类型筛选。"""
    where_clauses: list[str] = []
    parameters: list[str] = []

    normalized_keyword = (keyword or "").strip().lower()
    if normalized_keyword:
        where_clauses.append("LOWER(filename) LIKE ?")
        parameters.append(f"%{normalized_keyword}%")

    normalized_material_type = (material_type or "all").strip()
    if normalized_material_type == "视频":
        video_clause, video_parameters = build_extension_like_clause(MATERIAL_VIDEO_EXTENSIONS)
        where_clauses.append(video_clause)
        parameters.extend(video_parameters)
    elif normalized_material_type == "图片":
        image_clause, image_parameters = build_extension_like_clause(MATERIAL_IMAGE_EXTENSIONS)
        where_clauses.append(image_clause)
        parameters.extend(image_parameters)
    elif normalized_material_type == "其他":
        video_clause, video_parameters = build_extension_like_clause(MATERIAL_VIDEO_EXTENSIONS)
        image_clause, image_parameters = build_extension_like_clause(MATERIAL_IMAGE_EXTENSIONS)
        where_clauses.append(f"NOT ({video_clause} OR {image_clause})")
        parameters.extend(video_parameters)
        parameters.extend(image_parameters)

    if not where_clauses:
        return "", []
    return f" WHERE {' AND '.join(where_clauses)}", parameters


def build_material_order_clause(sort_by: str | None, sort_order: str | None) -> str:
    """构造素材排序 SQL，仅允许白名单字段，避免排序参数注入。"""
    sortable_columns = {
        "upload_time": "upload_time",
        "filesize": "filesize",
    }
    normalized_sort_by = sortable_columns.get((sort_by or "upload_time").strip(), "upload_time")
    normalized_sort_order = "ASC" if (sort_order or "desc").strip().lower() == "asc" else "DESC"
    return f"{normalized_sort_by} {normalized_sort_order}, id DESC"
