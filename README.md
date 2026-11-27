# 图书预约留架册

借阅台当班员用这套工作台处理图书待取右截尾估计与留架释放。进入工作台可调整本班复核额度，查看每张预约单的预测、命中规则和处置，导出单班可复算记录。

## 本地运行

```sh
docker compose up -d --build
```

访问 `http://127.0.0.1:18642`。样例是可复算的模拟班次，涵盖正常历史、较迟回执、最新冲突版、缺测单和临时分区。

```sh
docker compose exec -T app python -m shelfhold.entry evaluate --capacity 8 --strategy focus
docker compose exec -T app pytest -q
docker compose down --remove-orphans
```

[字段和时间窗](docs/SPEC.md) · [模块与回归表](docs/DEPTH.md) · [HTTP 与自备数据](docs/RUNBOOK.md)
