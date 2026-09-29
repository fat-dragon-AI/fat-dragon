# bench S3-v2-py38-nojieba

- set: `corpus`
- path_key: `py38-nojieba`  python=3.8.10  jieba=unavailable:No module named 'jieba'
- n=232  @1=214 (0.922414)  @3=230 (0.991379)  @10=232 (1.0)  空=0 (0.0)
- query p50=13.499 ms  p95=23.381 ms
- 核心 Top-1: 20/20

## @1 未命中（最多 40 条）
- '查一下有没有 nginx 进程' -> sys.process.find  got [['nginx.config.view', 24.5381, 'exact'], ['sys.process.list', 3.8, 'weak'], ['nginx.config.test', 24.6, 'exact'], ['nginx.reload', 14.6667, 'exact'], ['nginx.log', 10.2381, 'exact']]  rank=6
- 'nslookup交互' -> nslookup.interactive  got [['nslookup.lookup', 48.0889, 'exact'], ['nslookup.interactive', 45.396, 'exact'], ['nslookup.debug', 40.5769, 'exact'], ['nslookup.server', 20.0833, 'exact'], ['nslookup.reverse', 8.9778, 'exact']]  rank=1
- 'nginx 服务状态' -> svc.status  got [['nginx.config.view', 24.5381, 'exact'], ['svc.status', 6.5, 'weak'], ['nginx.config.test', 24.6, 'exact'], ['nginx.reload', 14.6667, 'exact'], ['nginx.log', 10.2381, 'exact']]  rank=1
- '启动 firewalld' -> svc.start  got [['firewall.status', 9.8, 'exact'], ['svc.start', 2.4, 'weak'], ['firewall.open.port', 8.5, 'exact']]  rank=1
- '停掉 redis' -> svc.stop  got [['redis.info', 29.5333, 'exact'], ['svc.stop', 2.4, 'weak'], ['redis.keys.sample', 20.1429, 'exact']]  rank=1
- '卸载 nginx' -> pkg.remove  got [['nginx.config.view', 24.5381, 'exact'], ['pkg.remove', 12.8, 'exact'], ['nginx.config.test', 24.6, 'exact'], ['nginx.reload', 15.8333, 'exact'], ['nginx.log', 10.2381, 'exact']]  rank=1
- 'which nginx' -> pkg.which  got [['nginx.config.view', 24.5381, 'exact'], ['pkg.which', 13.8667, 'exact'], ['nginx.config.test', 24.6, 'exact'], ['nginx.reload', 14.6667, 'exact'], ['nginx.log', 10.2381, 'exact']]  rank=1
- 'nginx装在哪' -> pkg.files  got [['nginx.config.view', 24.5381, 'exact'], ['pkg.files', 13.3, 'exact'], ['nginx.config.test', 24.6, 'exact'], ['nginx.reload', 14.6667, 'exact'], ['nginx.log', 10.2381, 'exact']]  rank=1
- 'nginx 配置校验一下' -> nginx.config.test  got [['nginx.config.view', 31.4071, 'exact'], ['nginx.config.test', 40.3083, 'exact'], ['nginx.reload', 16.9167, 'exact'], ['nginx.log', 10.2381, 'exact'], ['nginx.restart', 10.2333, 'exact']]  rank=1
- '重启 nginx' -> nginx.restart  got [['nginx.config.view', 24.5381, 'exact'], ['nginx.restart', 21.7333, 'exact'], ['nginx.config.test', 24.6, 'exact'], ['nginx.reload', 15.7917, 'exact'], ['nginx.log', 10.2381, 'exact']]  rank=1
- '看 nginx 错误日志' -> nginx.log  got [['nginx.config.view', 21.881, 'exact'], ['nginx.config.test', 24.6, 'exact'], ['nginx.reload', 14.6667, 'exact'], ['nginx.log', 13.6905, 'exact'], ['nginx.restart', 10.2333, 'exact']]  rank=3
- '没有jps怎么查java进程' -> java.ps  got [['jvm.jps', 51.0202, 'exact'], ['java.ps', 34.8143, 'exact'], ['java.version', 23.25, 'exact'], ['sys.process.list', 5.3, 'weak'], ['java.compile', 19.65, 'exact']]  rank=1
- '默认java是哪个' -> java.default.vm  got [['java.version', 30.0, 'exact'], ['java.default.vm', 17.6, 'exact'], ['jvm.jps', 26.4, 'exact'], ['java.compile', 19.65, 'exact'], ['java.ps', 15.7, 'exact']]  rank=1
- '切换java版本' -> java.switch.version  got [['java.version', 41.0786, 'exact'], ['java.switch.version', 38.2048, 'exact'], ['jvm.jps', 26.4, 'exact'], ['java.compile', 19.65, 'exact'], ['java.switch.home', 16.1286, 'exact']]  rank=1
- '临时切换java' -> java.switch.home  got [['java.switch.version', 29.3, 'exact'], ['java.switch.home', 27.6143, 'exact'], ['java.version', 23.25, 'exact'], ['jvm.jps', 26.4, 'exact'], ['java.compile', 19.65, 'exact']]  rank=1
- '看容器日志' -> docker.logs  got [['docker.ps', 29.0571, 'exact'], ['docker.logs', 25.0683, 'exact'], ['docker.exec', 20.7222, 'exact'], ['docker.images', 15.1143, 'exact'], ['docker.rm', 13.3286, 'exact']]  rank=1
- '改文件归属' -> perm.chown  got [['perm.owner.view', 78.15, 'exact'], ['perm.chown', 76.3167, 'exact'], ['echo.write.file', 4.1, 'weak']]  rank=1
- '临时加PATH' -> env.path.export  got [['env.path.write', 57.7167, 'exact'], ['env.path.export', 36.1714, 'exact'], ['env.path.view', 23.15, 'exact'], ['env.path.source', 11.7, 'exact']]  rank=1
