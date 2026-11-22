# 深度登记 · 馆藏媒介验收站

- 规模：中型
- 核心规则：在验收截点选定生效版本，将固化路径映射到阅览与冷存两层，对每层实际字节重算摘要。
- 使用者：馆藏迁移复核员对照原件、目标路径、观测行号及摘要，签署验收快照。

## 功能模块

| 模块 | 使用者动作 | 入口 | 核心文件 | 测试 |
|---|---|---|---|---|
| M1 馆藏批次 | 确认验收截点的生效策略 | `GET /api/batches/{sample}` | `app/modules/m1_batches/service.py` | `tests/test_batches.py` |
| M2 固化清单 | 查归一化原件和清单冲突 | `GET /api/manifest/{sample}` | `app/modules/m2_manifest/service.py` | `tests/test_manifest.py` |
| M3 路由映射 | 查命中前缀与目标层冲突 | `GET /api/mapping/{sample}` | `app/modules/m3_mapping/rules.py` | `tests/test_mapping.py` |
| M4 字节验签 | 查看观测时点、字节与摘要 | `GET /api/fixity/{sample}` | `app/modules/m4_fixity/service.py` | `tests/test_fixity.py` |
| M5 副本漂移 | 比较两层副本与固化值 | `GET /api/drift/{sample}` | `app/modules/m5_drift/classify.py` | `tests/test_drift.py` |
| M6 迁移勾稽 | 复核原件集合及状态计数 | `GET /api/reconcile/{sample}` | `app/modules/m6_reconcile/totals.py` | `tests/test_reconcile.py` |
| M7 复核封存 | 复算、签署、下载快照 | `POST /api/runs` | `app/modules/m7_archive/service.py` | `tests/test_archive.py` |

## 陷阱登记

| 陷阱 | 现象 | 朴素结果 | 处理 | 实现 | 测试 |
|---|---|---|---|---|---|
| TRAP-08 | 样例馆号前导零 | 编号错配 | 保留原串 | `app/modules/m2_manifest/service.py` | `tests/test_manifest.py::test_source_identifier_keeps_leading_zeros` |
| TRAP-09 | 巨型文件的申报字节数 | 浏览器精度丢失 | 整数累算后按字符串返回 | `app/modules/m2_manifest/service.py` | `tests/test_manifest.py::test_large_exact_bytes_are_strings` |
| TRAP-11 | 脏样例冷存观测用两种时区 | 重复验签 | 归并到同一 UTC 秒 | `app/modules/m4_fixity/service.py` | `tests/test_fixity.py::test_same_instant_has_same_key` |
| TRAP-13 | 未来观测混入当前封存批次 | 覆盖当前结果 | 截点过滤并保留证据 | `app/modules/m4_fixity/service.py` | `tests/test_fixity.py::test_future_scan_cannot_replace_current` |
| TRAP-14 | 同件不同申报摘要 | 后写覆盖 | 同 ID 归冲突并保留来源 | `app/modules/m2_manifest/service.py` | `tests/test_manifest.py::test_conflicting_fact_is_not_last_wins` |
| TRAP-16 | 副本字节串截断 | 垃圾字节被采信 | 严格解码并记录失败 | `app/modules/m4_fixity/bytes.py` | `tests/test_fixity.py::test_invalid_payload_is_quarantined` |
| TRAP-18 | 批次版本为空 | 生成无效通过报告 | 给出缺版状态 | `app/modules/m1_batches/service.py` | `tests/test_batches.py::test_missing_catalog_gives_explicit_state` |
| TRAP-19 | 根路由与照片子路由均命中 | 任取一条 | 路径段数最长优先 | `app/modules/m3_mapping/rules.py` | `tests/test_mapping.py::test_longest_annex_determines_target` |
| TRAP-21 | 脏样例缺少冷存 | 仅检查阅览后验收 | 逐层验证 | `app/modules/m5_drift/classify.py` | `tests/test_drift.py::test_missing_cold_copy_stays_pending` |
| TRAP-22 | 底片名使用两种 Unicode 表示 | 把重名当成两个路径 | NFC 后隔离冲突馆号 | `app/modules/m2_manifest/paths.py` | `tests/test_manifest.py::test_unicode_alias_collision_keeps_both_objects` |
| TRAP-23 | 版本恰好交接 | 同时激活两版 | 使用半开区间 | `app/modules/m1_batches/service.py` | `tests/test_batches.py::test_half_open_boundary_selects_new_release` |
| TRAP-25 | 两版有效期重叠 | 按文件次序选版本 | 拒绝选择并报告两版 | `app/modules/m1_batches/service.py` | `tests/test_batches.py::test_catalog_overlap_has_no_winner` |
| TRAP-26 | 提交旧摘要 | 签署错误证据 | 返回冲突 | `app/modules/m7_archive/service.py` | `tests/test_archive.py::test_signature_requires_current_digest` |
| TRAP-27 | 同内容多馆号归并同一路径 | 全部判冲突或静默合并丢号 | 确认共享副本组并保留全部馆号 | `app/modules/m2_manifest/service.py` | `tests/test_sharing.py::test_same_content_same_path_forms_share_group` |
