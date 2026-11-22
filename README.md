# 馆藏媒介验收站

供馆藏迁移复核员核对固化原件、阅览副本和冷存副本。矩阵可筛选结果、点选馆号，并查看原件预期摘要、目标路径、实测摘要和对应观测行。

## 启动

```sh
docker compose up --build
```

打开 `http://localhost:18447`。应用内置干净和现场样例，可导入同结构 JSON。运行验收后，在复核封存面板复算、签署或下载冻结证据。命名卷保存运行和签署记录。API 说明见 `/docs`。

宿主执行 `pip install -r requirements.txt` 后可运行 `uvicorn app.main:app --port 18447` 或 `pytest -q`。容器测试执行 `docker compose exec -T app pytest -q`。

小批量验收使用 JSON 内联字节，单行载荷上限 175,000 个 Base64 字符。批次总大小上限 3 MB。字段见 [数据字典](docs/DATA-DICTIONARY.md)，模块和用例见 [深度登记](docs/DEPTH.md)。
