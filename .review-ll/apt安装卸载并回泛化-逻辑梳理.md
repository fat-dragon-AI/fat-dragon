# apt 源安装/卸载并回泛化 — 逻辑梳理

```
安装软件 / apt安装 / yum安装  → pkg.install  → {pkg_install}（按发行版）
卸载软件 / apt卸载 / yum remove → pkg.remove → {pkg_remove} / {pkg_purge}
安装deb / dpkg -i             → pkg.dpkg.install（本地文件，不并入 install）
apt彻底卸载 / purge           → pkg.apt.purge（语义不同，不并入 remove）
```

原则：同一操作只留一个 intent；工具名（apt/yum）是同义词，不是新意图。专用规则只覆盖泛化占位符盖不住的差异。
