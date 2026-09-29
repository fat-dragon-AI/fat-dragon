# bench S8-core-py38

- set: `core`
- path_key: `py38-nojieba`  python=3.8.10  jieba=unavailable:No module named 'jieba'
- n=20  @1=20 (1.0)  @3=20 (1.0)  @10=20 (1.0)  空=0 (0.0)
- query p50=4.15 ms  p95=10.564 ms
- 核心 Top-1: 20/20
- recall@30=1.0  containment=1.0
