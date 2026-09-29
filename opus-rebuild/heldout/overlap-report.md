# held-out overlap 报告

- 文件：`opus-rebuild/heldout/heldout-v1.jsonl`
- 口径：NFKC + 去空白 + lower；全库 keyword len≥2；硬驳回 kw_in_query / query_in_kw
- 规则 213 条 / 原始 keyword 1534 / 归一化 unique len≥2 = 1510
- 条数 n_total=132 n_scored=120 n_noisy=12
- 硬驳回：**0**
- 期望规则 keyword 副口径命中：0
- desc LCS≥4 软告警：6

## 硬驳回明细
无。

## 副口径（仅期望规则 keyword，应为空）
无重叠。

## 软告警（与期望 desc 最长公共子串 ≥4）
- `ho-016` 取消开机后自己起来 → svc.disable（desc「取消开机自启」，lcs=4）
- `ho-019` 进入jar包 → java.jar.inspect（desc「查看 jar 包内容/清单」，lcs=4）
- `ho-038` 查找firefox的安装位置 → pkg.files（desc「查看软件本体 / 包内文件安装位置」，lcs=4）
- `ho-062` 上一条命令成功了没有，返回几 → echo.exit.status（desc「查看上一条命令退出码」，lcs=5）
- `ho-090` 在文件末尾再添一句 → text.append.line（desc「向文件末尾追加一行文本」，lcs=4）
- `ho-104` 修改文件用户权限 → perm.chmod（desc「修改文件权限（示例）」，lcs=4）

