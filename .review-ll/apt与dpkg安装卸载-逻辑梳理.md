# apt / dpkg 安装卸载 — 逻辑梳理

源安装 / 普通卸载已并回泛化，见 [apt安装卸载并回泛化-逻辑梳理.md](./apt安装卸载并回泛化-逻辑梳理.md)。

```
安装deb / dpkg -i / purge / update / autoremove
  → pkg.dpkg.* | pkg.apt.purge | pkg.apt.update | pkg.apt.autoremove
  → extract: pkg 或 path（.deb）
```

`dpkg -i` sequence 的 `stop_on_error=false`：缺依赖时第一步常非 0，第二步 `-f` 才修。
