# bench S1-corpus-py39-jieba

- set: `corpus`
- path_key: `py39-jieba`  python=3.9.18  jieba=ready
- n=232  @1=213 (0.918103)  @3=229 (0.987069)  @10=232 (1.0)  空=0 (0.0)
- query p50=18.847 ms  p95=35.018 ms
- 核心 Top-1: 20/20

## @1 未命中（最多 40 条）
- '查一下有没有 nginx 进程' -> sys.process.find  got [['nginx.config.view', 28.0381, 'exact'], ['sys.process.list', 4.325, 'weak'], ['nginx.config.test', 28.1, 'exact'], ['nginx.restart', 27.7833, 'exact'], ['nginx.log', 25.9381, 'exact']]  rank=6
- 'nslookup交互' -> nslookup.interactive  got [['nslookup.lookup', 50.8889, 'exact'], ['nslookup.interactive', 49.596, 'exact'], ['nslookup.debug', 40.5769, 'exact'], ['nslookup.server', 20.0833, 'exact'], ['nslookup.reverse', 8.9778, 'exact']]  rank=1
- '找一下叫 application.yml 的文件' -> file.find.name  got [['ollama.version', 8.1, 'exact'], ['mvn.version', 8.0, 'exact'], ['java.version', 7.8, 'weak'], ['svc.unit.cat', 7.7, 'weak'], ['pkg.dpkg.install', 7.3, 'weak']]  rank=6
- 'nginx 服务状态' -> svc.status  got [['nginx.config.view', 28.0381, 'exact'], ['svc.status', 7.9, 'weak'], ['nginx.config.test', 28.1, 'exact'], ['nginx.restart', 27.7833, 'exact'], ['nginx.log', 25.9381, 'exact']]  rank=1
- '启动 firewalld' -> svc.start  got [['firewall.status', 12.95, 'exact'], ['svc.start', 2.925, 'weak'], ['firewall.open.port', 8.5, 'exact'], ['pkg.dpkg.install', 7.3, 'weak'], ['pkg.dpkg.remove', 7.3, 'weak']]  rank=1
- '停掉 redis' -> svc.stop  got [['redis.info', 33.0333, 'exact'], ['svc.stop', 2.925, 'weak'], ['redis.keys.sample', 23.6429, 'exact'], ['pkg.dpkg.install', 7.3, 'weak'], ['pkg.dpkg.remove', 7.3, 'weak']]  rank=1
- '卸载 nginx' -> pkg.remove  got [['nginx.config.view', 28.0381, 'exact'], ['pkg.remove', 16.3, 'exact'], ['nginx.config.test', 28.1, 'exact'], ['nginx.restart', 27.7833, 'exact'], ['nginx.log', 25.9381, 'exact']]  rank=1
- 'which nginx' -> pkg.which  got [['nginx.config.view', 28.0381, 'exact'], ['pkg.which', 16.6667, 'exact'], ['nginx.config.test', 28.1, 'exact'], ['nginx.restart', 27.7833, 'exact'], ['nginx.log', 25.9381, 'exact']]  rank=1
- 'nginx装在哪' -> pkg.files  got [['nginx.config.view', 28.0381, 'exact'], ['pkg.files', 16.1, 'exact'], ['nginx.config.test', 28.1, 'exact'], ['nginx.restart', 27.7833, 'exact'], ['nginx.log', 25.9381, 'exact']]  rank=1
- 'nginx 配置校验一下' -> nginx.config.test  got [['nginx.config.view', 34.9071, 'exact'], ['nginx.config.test', 43.8083, 'exact'], ['nginx.restart', 27.7833, 'exact'], ['nginx.log', 25.9381, 'exact'], ['nginx.reload', 21.1167, 'exact']]  rank=1
- '看 nginx 错误日志' -> nginx.log  got [['nginx.config.view', 25.381, 'exact'], ['nginx.log', 29.3905, 'exact'], ['nginx.config.test', 28.1, 'exact'], ['nginx.restart', 27.7833, 'exact'], ['nginx.reload', 18.8667, 'exact']]  rank=1
- '没有jps怎么查java进程' -> java.ps  got [['jvm.jps', 55.8536, 'exact'], ['java.ps', 44.9143, 'exact'], ['java.version', 24.65, 'exact'], ['sys.process.list', 6.525, 'weak'], ['java.home.env', 21.2, 'exact']]  rank=1
- '默认java是哪个' -> java.default.vm  got [['java.version', 31.4, 'exact'], ['java.default.vm', 19.7, 'exact'], ['jvm.jps', 26.4, 'exact'], ['java.home.env', 21.2, 'exact'], ['java.ps', 20.2, 'exact']]  rank=1
- '切换java版本' -> java.switch.version  got [['java.version', 43.1786, 'exact'], ['java.switch.version', 41.0048, 'exact'], ['jvm.jps', 26.4, 'exact'], ['java.home.env', 21.2, 'exact'], ['java.ps', 20.2, 'exact']]  rank=1
- '临时切换java' -> java.switch.home  got [['java.switch.version', 31.4, 'exact'], ['java.switch.home', 30.4143, 'exact'], ['java.version', 24.65, 'exact'], ['jvm.jps', 26.4, 'exact'], ['java.home.env', 21.2, 'exact']]  rank=1
- '看容器日志' -> docker.logs  got [['docker.ps', 37.4571, 'exact'], ['docker.logs', 32.4183, 'exact'], ['docker.images', 26.1643, 'exact'], ['docker.exec', 24.5722, 'exact'], ['docker.compose.ps', 23.7, 'exact']]  rank=1
- '改文件归属' -> perm.chown  got [['perm.owner.view', 98.45, 'exact'], ['perm.chown', 94.8667, 'exact'], ['sys.mem.free', 4.5, 'weak'], ['echo.no.newline', 4.4, 'weak'], ['echo.write.file', 4.1, 'weak']]  rank=1
- '临时加PATH' -> env.path.export  got [['env.path.write', 59.4667, 'exact'], ['env.path.export', 38.6214, 'exact'], ['env.path.view', 29.05, 'exact'], ['env.path.source', 17.2, 'exact'], ['pkg.dpkg.purge', 7.3, 'weak']]  rank=1
- 'docker' -> docker.ps  got [['docker.images', 31.6643, 'exact'], ['docker.exec', 31.0722, 'exact'], ['docker.logs', 30.7754, 'exact'], ['docker.ps', 30.4929, 'exact'], ['docker.compose.ps', 26.7, 'exact']]  rank=3
