# 基准测试集

将成对文件放入子目录，例如：

```
line_charts/
  chart_01.png
  chart_01_truth.csv
  chart_01_pred.csv   # 由导出结果生成
```

运行：

```bash
cd backend && python tests/benchmark/run_benchmark.py --dir tests/benchmark/line_charts
```
