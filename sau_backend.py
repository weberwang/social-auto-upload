import asyncio
import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from queue import Queue
from flask_cors import CORS
from myUtils.auth import check_cookie
from myUtils.material_records import (
    build_material_filter_clause,
    build_material_order_clause,
    ensure_file_records_schema,
    parse_positive_int,
    serialize_material_row,
    should_use_paginated_material_query,
)
from flask import Flask, request, jsonify, Response, render_template, send_from_directory, g
from werkzeug.utils import secure_filename
from conf import BASE_DIR
from myUtils.login import bilibili_cookie_gen, get_tencent_cookie, douyin_cookie_gen, get_ks_cookie, xiaohongshu_cookie_gen
from myUtils.publish_drafts import (
    PublishDraftError,
    delete_publish_draft,
    get_publish_draft,
    list_publish_drafts,
    save_publish_draft,
)
from myUtils.web_publish import PublishRequestError, dispatch_web_publish_request, parse_web_publish_request
from utils.log import bilibili_logger

active_queues = {}
app = Flask(__name__)

#允许所有来源跨域访问
CORS(app)

# 限制上传文件大小为160MB
app.config['MAX_CONTENT_LENGTH'] = 160 * 1024 * 1024

# 获取当前目录（假设 index.html 和 assets 在这里）
current_dir = os.path.dirname(os.path.abspath(__file__))


@app.before_request
def record_request_start_time():
    """记录请求开始时间，供统一访问日志计算耗时。"""
    g.request_started_at = time.perf_counter()


@app.after_request
def log_request_summary(response):
    """输出统一访问日志，确保非 debug 模式下也能看到请求明细。"""
    started_at = getattr(g, "request_started_at", None)
    duration_ms = 0.0
    if started_at is not None:
        # 使用高精度计时器统计请求耗时，避免受系统时钟调整影响。
        duration_ms = (time.perf_counter() - started_at) * 1000

    print(
        f"[REQ] {request.method} {request.path} -> {response.status_code} {duration_ms:.1f}ms",
        flush=True,
    )
    return response


def get_video_storage_dir(create: bool = False) -> Path:
    """返回视频上传目录，并在需要写入时按需创建目录。"""
    video_dir = Path(BASE_DIR / "videoFile")
    if create:
        # 前端上传接口依赖该目录存在，启动脚本未准备目录时在这里兜底创建。
        video_dir.mkdir(parents=True, exist_ok=True)
    return video_dir

# 处理所有静态资源请求（未来打包用）
@app.route('/assets/<filename>')
def custom_static(filename):
    return send_from_directory(os.path.join(current_dir, 'assets'), filename)

# 处理 favicon.ico 静态资源（未来打包用）
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')

@app.route('/vite.svg')
def vite_svg():
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')

# （未来打包用）
@app.route('/')
def index():  # put application's code here
    return send_from_directory(current_dir, 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """接收单个文件上传，并返回可用于后续发布的文件标识。"""
    if 'file' not in request.files:
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No file part in the request"
        }), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No selected file"
        }), 400
    try:
        # 保存文件到指定位置
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        safe_name = secure_filename(file.filename)
        if not safe_name:
            return jsonify({"code": 400, "data": None, "msg": "Invalid filename"}), 400
        filepath = get_video_storage_dir(create=True) / f"{uuid_v1}_{safe_name}"
        file.save(filepath)
        return jsonify({"code":200,"msg": "File uploaded successfully", "data": f"{uuid_v1}_{safe_name}"}), 200
    except Exception as e:
        return jsonify({"code":500,"msg": str(e),"data":None}), 500

@app.route('/getFile', methods=['GET'])
def get_file():
    """按文件名返回已上传素材，供前端直接预览。"""
    # 获取 filename 参数
    filename = request.args.get('filename')

    if not filename:
        return jsonify({"code": 400, "msg": "filename is required", "data": None}), 400

    # 防止路径穿越攻击
    if '..' in filename or filename.startswith('/'):
        return jsonify({"code": 400, "msg": "Invalid filename", "data": None}), 400

    # 拼接完整路径
    file_path = str(get_video_storage_dir())

    # 返回文件
    return send_from_directory(file_path,filename)


@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """按文件名下载已上传素材，供预览弹窗回退到本地下载。"""
    if not filename:
        return jsonify({"code": 400, "msg": "filename is required", "data": None}), 400

    if '..' in filename or filename.startswith('/'):
        return jsonify({"code": 400, "msg": "Invalid filename", "data": None}), 400

    return send_from_directory(str(get_video_storage_dir()), filename, as_attachment=True)


@app.route('/uploadSave', methods=['POST'])
def upload_save():
    """上传文件并同步写入文件记录表。"""
    if 'file' not in request.files:
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No file part in the request"
        }), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No selected file"
        }), 400

    remark = (request.form.get('remark') or '').strip()
    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"code": 400, "data": None, "msg": "Invalid filename"}), 400

    try:
        # 生成 UUID v1
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")

        # 构造文件名和路径
        final_filename = f"{uuid_v1}_{filename}"
        filepath = get_video_storage_dir(create=True) / final_filename

        # 保存文件
        file.save(filepath)

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            ensure_file_records_schema(conn)
            cursor = conn.cursor()
            cursor.execute('''
                                INSERT INTO file_records (filename, filesize, file_path, remark)
            VALUES (?, ?, ?, ?)
                                ''', (filename, round(float(os.path.getsize(filepath)) / (1024 * 1024),2), final_filename, remark))
            conn.commit()
            print("✅ 上传文件已记录")

        return jsonify({
            "code": 200,
            "msg": "File uploaded and saved successfully",
            "data": {
                "filename": filename,
                "filepath": final_filename,
                "remark": remark
            }
        }), 200

    except Exception as e:
        print(f"Upload failed: {e}")
        return jsonify({
            "code": 500,
            "msg": f"upload failed: {e}",
            "data": None
        }), 500

@app.route('/getFiles', methods=['GET'])
def get_all_files():
    try:
        # 使用 with 自动管理数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row  # 允许通过列名访问结果
            ensure_file_records_schema(conn)
            cursor = conn.cursor()

            if not should_use_paginated_material_query(request.args):
                # 保留旧版全量返回行为，避免仪表盘和发布中心被这次分页改造联动打断。
                cursor.execute("SELECT * FROM file_records")
                rows = cursor.fetchall()
                return jsonify({
                    "code": 200,
                    "msg": "success",
                    "data": [serialize_material_row(row) for row in rows]
                }), 200

            page = parse_positive_int(request.args.get("page"), 1)
            page_size = parse_positive_int(request.args.get("page_size"), 20)
            keyword = request.args.get("keyword")
            material_type = request.args.get("material_type")
            sort_by = request.args.get("sort_by")
            sort_order = request.args.get("sort_order")
            where_clause, filter_parameters = build_material_filter_clause(keyword, material_type)
            order_clause = build_material_order_clause(sort_by, sort_order)

            # 分页查询先查总数，再按页拉取明细，避免前端无法显示完整页码信息。
            cursor.execute(
                f"SELECT COUNT(*) AS total FROM file_records{where_clause}",
                filter_parameters,
            )
            total_count = int(cursor.fetchone()["total"])
            total_pages = 0 if total_count == 0 else (total_count + page_size - 1) // page_size
            offset = (page - 1) * page_size

            cursor.execute(
                f"SELECT * FROM file_records{where_clause} ORDER BY {order_clause} LIMIT ? OFFSET ?",
                [*filter_parameters, page_size, offset],
            )
            rows = cursor.fetchall()

            return jsonify({
                "code": 200,
                "msg": "success",
                "data": [serialize_material_row(row) for row in rows],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total_count,
                    "total_pages": total_pages,
                }
            }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("get file failed!"),
            "data": None
        }), 500


@app.route("/getAccounts", methods=['GET'])
def getAccounts():
    """快速获取所有账号信息，不进行cookie验证"""
    try:
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
            SELECT * FROM user_info''')
            rows = cursor.fetchall()
            rows_list = [list(row) for row in rows]

            print("\n📋 当前数据表内容（快速获取）：")
            for row in rows:
                print(row)

            return jsonify(
                {
                    "code": 200,
                    "msg": None,
                    "data": rows_list
                }), 200
    except Exception as e:
        print(f"获取账号列表时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"获取账号列表失败: {str(e)}",
            "data": None
        }), 500


@app.route("/getValidAccounts",methods=['GET'])
async def getValidAccounts():
    with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT * FROM user_info''')
        rows = cursor.fetchall()
        rows_list = [list(row) for row in rows]
        print("\n📋 当前数据表内容：")
        for row in rows:
            print(row)
        for row in rows_list:
            flag = await check_cookie(row[1],row[2])
            if not flag:
                row[4] = 0
                cursor.execute('''
                UPDATE user_info 
                SET status = ? 
                WHERE id = ?
                ''', (0,row[0]))
                conn.commit()
                print("✅ 用户状态已更新")
        for row in rows:
            print(row)
        return jsonify(
                        {
                            "code": 200,
                            "msg": None,
                            "data": rows_list
                        }),200

@app.route('/deleteFile', methods=['GET'])
def delete_file():
    """删除文件记录，并尽量同步清理磁盘上的实际文件。"""
    file_id = request.args.get('id')

    if not file_id or not file_id.isdigit():
        return jsonify({
            "code": 400,
            "msg": "Invalid or missing file ID",
            "data": None
        }), 400

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM file_records WHERE id = ?", (file_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "File not found",
                    "data": None
                }), 404

            record = dict(record)

            # 获取文件路径并删除实际文件
            file_path = get_video_storage_dir() / record['file_path']
            if file_path.exists():
                try:
                    file_path.unlink()  # 删除文件
                    print(f"✅ 实际文件已删除: {file_path}")
                except Exception as e:
                    print(f"⚠️ 删除实际文件失败: {e}")
                    # 即使删除文件失败，也要继续删除数据库记录，避免数据不一致
            else:
                print(f"⚠️ 实际文件不存在: {file_path}")

            # 删除数据库记录
            cursor.execute("DELETE FROM file_records WHERE id = ?", (file_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "File deleted successfully",
            "data": {
                "id": record['id'],
                "filename": record['filename']
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("delete failed!"),
            "data": None
        }), 500

@app.route('/deleteAccount', methods=['GET'])
def delete_account():
    account_id = request.args.get('id')

    if not account_id or not account_id.isdigit():
        return jsonify({
            "code": 400,
            "msg": "Invalid or missing account ID",
            "data": None
        }), 400

    account_id = int(account_id)

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM user_info WHERE id = ?", (account_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "account not found",
                    "data": None
                }), 404

            record = dict(record)

            # 删除关联的cookie文件
            if record.get('filePath'):
                cookie_file_path = Path(BASE_DIR / "cookiesFile" / record['filePath'])
                if cookie_file_path.exists():
                    try:
                        cookie_file_path.unlink()
                        print(f"✅ Cookie文件已删除: {cookie_file_path}")
                    except Exception as e:
                        print(f"⚠️ 删除Cookie文件失败: {e}")

            # 删除数据库记录
            cursor.execute("DELETE FROM user_info WHERE id = ?", (account_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account deleted successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"delete failed: {str(e)}",
            "data": None
        }), 500


# SSE 登录接口
@app.route('/login')
def login():
    # 1 小红书 2 视频号 3 抖音 4 快手 5 B站
    type = request.args.get('type')
    # 账号名
    id = request.args.get('id')

    # 模拟一个用于异步通信的队列
    status_queue = Queue()
    active_queues[id] = status_queue

    def on_close():
        print(f"清理队列: {id}")
        del active_queues[id]
    # 启动异步任务线程
    thread = threading.Thread(target=run_async_function, args=(type,id,status_queue), daemon=True)
    thread.start()
    response = Response(sse_stream(status_queue,), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # 关键：禁用 Nginx 缓冲
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Connection'] = 'keep-alive'
    return response

@app.route('/postVideo', methods=['POST'])
def postVideo():
    try:
        publish_request = parse_web_publish_request(request.get_json())
        print("File List:", list(publish_request.file_list))
        print("Account List:", list(publish_request.account_list))
        dispatch_web_publish_request(publish_request)
        return jsonify(
            {
                "code": 200,
                "msg": "发布任务已提交",
                "data": None
            }), 200
    except PublishRequestError as e:
        return jsonify({
            "code": 400,
            "msg": str(e),
            "data": None
        }), 400
    except Exception as e:
        print(f"发布视频时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"发布失败: {str(e)}",
            "data": None
        }), 500


@app.route("/savePublishDraft", methods=["POST"])
def save_publish_draft_endpoint():
    """保存发布中心草稿，支持新建与覆盖已有草稿。"""

    try:
        draft = save_publish_draft(Path(BASE_DIR), request.get_json())
        return jsonify(
            {
                "code": 200,
                "msg": "草稿保存成功",
                "data": draft,
            }
        ), 200
    except PublishDraftError as error:
        return jsonify({"code": error.status_code, "msg": str(error), "data": None}), error.status_code
    except Exception as error:
        print(f"保存发布草稿时出错: {error}")
        return jsonify({"code": 500, "msg": f"保存草稿失败: {error}", "data": None}), 500


@app.route("/getPublishDrafts", methods=["GET"])
def get_publish_drafts_endpoint():
    """返回发布中心草稿列表，供前端弹窗选择要加载的工作区。"""

    try:
        drafts = list_publish_drafts(Path(BASE_DIR))
        return jsonify({"code": 200, "msg": "success", "data": drafts}), 200
    except PublishDraftError as error:
        return jsonify({"code": error.status_code, "msg": str(error), "data": None}), error.status_code
    except Exception as error:
        print(f"获取发布草稿列表时出错: {error}")
        return jsonify({"code": 500, "msg": f"获取草稿列表失败: {error}", "data": None}), 500


@app.route("/getPublishDraft", methods=["GET"])
def get_publish_draft_endpoint():
    """返回单个草稿详情，供发布中心完整回填全部 Tab 状态。"""

    try:
        draft = get_publish_draft(Path(BASE_DIR), request.args.get("id"))
        return jsonify({"code": 200, "msg": "success", "data": draft}), 200
    except PublishDraftError as error:
        return jsonify({"code": error.status_code, "msg": str(error), "data": None}), error.status_code
    except Exception as error:
        print(f"获取发布草稿详情时出错: {error}")
        return jsonify({"code": 500, "msg": f"获取草稿详情失败: {error}", "data": None}), 500


@app.route("/deletePublishDraft", methods=["GET"])
def delete_publish_draft_endpoint():
    """删除指定草稿，避免前端继续展示已废弃的工作区快照。"""

    try:
        result = delete_publish_draft(Path(BASE_DIR), request.args.get("id"))
        return jsonify({"code": 200, "msg": "草稿删除成功", "data": result}), 200
    except PublishDraftError as error:
        return jsonify({"code": error.status_code, "msg": str(error), "data": None}), error.status_code
    except Exception as error:
        print(f"删除发布草稿时出错: {error}")
        return jsonify({"code": 500, "msg": f"删除草稿失败: {error}", "data": None}), 500


@app.route('/updateUserinfo', methods=['POST'])
def updateUserinfo():
    # 获取JSON数据
    data = request.get_json()

    # 从JSON数据中提取 type 和 userName
    user_id = data.get('id')
    type = data.get('type')
    userName = data.get('userName')
    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 更新数据库记录
            cursor.execute('''
                           UPDATE user_info
                           SET type     = ?,
                               userName = ?
                           WHERE id = ?;
                           ''', (type, userName, user_id))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "account update successfully",
            "data": None
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("update failed!"),
            "data": None
        }), 500

@app.route('/postVideoBatch', methods=['POST'])
def postVideoBatch():
    data_list = request.get_json()

    if not isinstance(data_list, list):
        return jsonify({"code": 400, "msg": "Expected a JSON array", "data": None}), 400
    try:
        for data in data_list:
            publish_request = parse_web_publish_request(data)
            print("File List:", list(publish_request.file_list))
            print("Account List:", list(publish_request.account_list))
            dispatch_web_publish_request(publish_request)
    except PublishRequestError as e:
        return jsonify({"code": 400, "msg": str(e), "data": None}), 400
    # 返回响应给客户端
    return jsonify(
        {
            "code": 200,
            "msg": None,
            "data": None
        }), 200

# Cookie文件上传API
@app.route('/uploadCookie', methods=['POST'])
def upload_cookie():
    try:
        if 'file' not in request.files:
            return jsonify({
                "code": 400,
                "msg": "没有找到Cookie文件",
                "data": None
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "code": 400,
                "msg": "Cookie文件名不能为空",
                "data": None
            }), 400

        if not file.filename.endswith('.json'):
            return jsonify({
                "code": 400,
                "msg": "Cookie文件必须是JSON格式",
                "data": None
            }), 400

        # 获取账号信息
        account_id = request.form.get('id')
        platform = request.form.get('platform')

        if not account_id or not platform:
            return jsonify({
                "code": 400,
                "msg": "缺少账号ID或平台信息",
                "data": None
            }), 400

        # 从数据库获取账号的文件路径
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT filePath FROM user_info WHERE id = ?', (account_id,))
            result = cursor.fetchone()

        if not result:
            return jsonify({
                "code": 500,
                "msg": "账号不存在",
                "data": None
            }), 404

        # 保存上传的Cookie文件到对应路径
        cookie_file_path = Path(BASE_DIR / "cookiesFile" / result['filePath'])
        cookie_file_path.parent.mkdir(parents=True, exist_ok=True)

        file.save(str(cookie_file_path))

        # 更新数据库中的账号信息（可选，比如更新更新时间）
        # 这里可以根据需要添加额外的处理逻辑

        return jsonify({
            "code": 200,
            "msg": "Cookie文件上传成功",
            "data": None
        }), 200

    except Exception as e:
        print(f"上传Cookie文件时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"上传Cookie文件失败: {str(e)}",
            "data": None
        }), 500


# Cookie文件下载API
@app.route('/downloadCookie', methods=['GET'])
def download_cookie():
    try:
        file_path = request.args.get('filePath')
        if not file_path:
            return jsonify({
                "code": 500,
                "msg": "缺少文件路径参数",
                "data": None
            }), 400

        # 验证文件路径的安全性，防止路径遍历攻击
        cookie_file_path = Path(BASE_DIR / "cookiesFile" / file_path).resolve()
        base_path = Path(BASE_DIR / "cookiesFile").resolve()

        if not cookie_file_path.is_relative_to(base_path):
            return jsonify({
                "code": 500,
                "msg": "非法文件路径",
                "data": None
            }), 400

        if not cookie_file_path.exists():
            return jsonify({
                "code": 500,
                "msg": "Cookie文件不存在",
                "data": None
            }), 404

        # 返回文件
        return send_from_directory(
            directory=str(cookie_file_path.parent),
            path=cookie_file_path.name,
            as_attachment=True
        )

    except Exception as e:
        print(f"下载Cookie文件时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"下载Cookie文件失败: {str(e)}",
            "data": None
        }), 500


# 包装函数：在线程中运行异步函数
def run_async_function(type,id,status_queue):
    try:
        match type:
            case '1':
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(xiaohongshu_cookie_gen(id, status_queue))
                loop.close()
            case '2':
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(get_tencent_cookie(id,status_queue))
                loop.close()
            case '3':
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(douyin_cookie_gen(id,status_queue))
                loop.close()
            case '4':
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(get_ks_cookie(id,status_queue))
                loop.close()
            case '5':
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(bilibili_cookie_gen(id, status_queue))
                loop.close()
    except Exception as exc:
        # 线程内异常如果不兜底，前端只能看到超时或空白，这里统一落日志并回传摘要。
        bilibili_logger.exception(f"历史 Web 登录线程异常，平台类型={type}，账号名={id}，错误={exc}")
        status_queue.put(f"ERROR:登录线程异常：{exc}")
        status_queue.put("500")

# SSE 流生成器函数
def sse_stream(status_queue):
    while True:
        if not status_queue.empty():
            msg = status_queue.get()
            yield f"data: {msg}\n\n"
        else:
            # 避免 CPU 占满
            time.sleep(0.1)

if __name__ == '__main__':
    app.run(host='0.0.0.0' ,port=5409)
