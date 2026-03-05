# 项目结构

```text
database.db         # 本地开发数据库（SQLite）
project.md          # 项目结构说明
pyproject.toml      # 依赖与项目元信息
uv.lock             # 依赖锁文件
scripts/            # 运维/脚本（当前为空）
src/                # 代码根目录
    core/           # 配置/日志/安全
        config.py
        logging.py
        security.py
    db/             # 数据库连接与初始化
        _db.py
        init.py
        models.py
        through/
            account.py
            permissions.py
    auth/           # 认证与权限领域
        user/
            account.py
            schemas.py
        permissions/
            group/
                schemas.py
            scopes/
                schemas.py
        sessions/
            token/
                jwt.py
                oauth2.py
                resolve.py
                schemas.py
    myapp/          # FastAPI 应用层
        main.py     # 应用入口
        router.py   # API 路由聚合
        cli/
            create_new_modules.py
        common/
        modules/    # 业务模块
            chat/
                api/
                    router.py
                    routes/
                schemas/
                services/
            profiles/
                api/
                    router.py
                    routes/
                schemas/
                services/
```

说明：
- 模块脚手架由 `src/myapp/cli/create_new_modules.py` 生成，完整目录会包含 `domain/`、`persistence/` 等子目录；当前已存在的模块为精简结构。

# 整体待办

1. 补全日志与安全相关实现（见 `core/logging.py`、`core/security.py` 中的 TODO）。
2. 完善认证与权限细节（见 `auth/` 与 `auth/sessions/` 内的 TODO）。
3. 继续扩展 `myapp/modules` 业务模块与 API。

# 项目规范

1. 以 `src/` 为包根进行导入，跨包使用绝对导入：`from core ...`、`from auth ...`、`from db ...`、`from myapp ...`。
2. 同一子包内部可用相对导入。
3. 所有业务路由在 `myapp/router.py` 统一聚合与挂载。
