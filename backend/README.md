# Backend

FastAPI 后端骨架，负责主题管理、文章查询、每日简报、数据采集和摘要生成。

## 本地启动

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## 开发命令

```bash
ruff check app tests
pytest
```
