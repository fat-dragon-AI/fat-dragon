# bench S8-corpus-py38

- set: `corpus`
- path_key: `py38-nojieba`  python=3.8.10  jieba=unavailable:No module named 'jieba'
- n=232  @1=224 (0.965517)  @3=229 (0.987069)  @10=232 (1.0)  空=0 (0.0)
- query p50=3.425 ms  p95=5.218 ms
- 核心 Top-1: 20/20
- recall@30=1.0  containment=1.0

## @1 未命中（最多 40 条）
- '查一下有没有 nginx 进程' -> sys.process.find  got [['nginx.config.view', 0.3905, 'exact'], ['nginx.log', 0.2777, 'weak'], ['nginx.restart', 0.2754, 'weak'], ['nginx.config.test', 0.2648, 'weak'], ['nginx.reload', 0.2633, 'weak']]  rank=5
- 'nginx 服务状态' -> svc.status  got [['nginx.config.view', 0.5516, 'weak'], ['svc.status', 0.5025, 'weak'], ['nginx.log', 0.3923, 'weak'], ['nginx.restart', 0.389, 'weak'], ['nginx.config.test', 0.3741, 'weak']]  rank=1
- '启动 firewalld' -> svc.start  got [['firewall.status', 0.8359, 'exact'], ['firewall.open.port', 0.5793, 'weak'], ['im.fcitx.restart', 0.2556, 'weak'], ['svc.start', 0.1346, 'weak'], ['pkg.install', 0.1318, 'weak']]  rank=3
- '停掉 redis' -> svc.stop  got [['redis.info', 0.6305, 'exact'], ['redis.keys.sample', 0.5004, 'weak'], ['svc.stop', 0.2833, 'weak'], ['svc.disable', 0.1504, 'weak'], ['docker.stop', 0.1227, 'weak']]  rank=2
- '卸载 nginx' -> pkg.remove  got [['nginx.reload', 0.7286, 'weak'], ['nginx.config.view', 0.6546, 'weak'], ['nginx.log', 0.4655, 'weak'], ['nginx.restart', 0.4617, 'weak'], ['nginx.config.test', 0.4439, 'weak']]  rank=5
- 'nginx装在哪' -> pkg.files  got [['nginx.config.view', 0.5501, 'weak'], ['pkg.files', 0.5066, 'weak'], ['nginx.log', 0.3912, 'weak'], ['nginx.restart', 0.388, 'weak'], ['nginx.config.test', 0.373, 'weak']]  rank=1
- '看 nginx 错误日志' -> nginx.log  got [['nginx.config.view', 0.5493, 'exact'], ['nginx.log', 0.4648, 'weak'], ['nginx.restart', 0.3138, 'weak'], ['nginx.config.test', 0.3018, 'weak'], ['nginx.reload', 0.3, 'weak']]  rank=1
- '默认java是哪个' -> java.default.vm  got [['java.version', 0.6709, 'weak'], ['java.default.vm', 0.647, 'weak'], ['java.switch.version', 0.3105, 'weak'], ['java.compile', 0.2191, 'weak'], ['java.ps', 0.1666, 'weak']]  rank=1
