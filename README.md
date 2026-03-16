# porter_bench

A Python benchmarking library for measuring execution time and memory usage across named pipeline steps and training loop iterations.

## Installation

```bash
pip install -e ".[dev]"
pre-commit install
# or
make install
```

## Quick start

```python
from porter_bench import bench_dict

for i in range(10):
    bench_dict["my_pipeline"].gstep()   # boundary between iterations

    data = load()
    bench_dict["my_pipeline"].step("load")

    result = process(data)
    bench_dict["my_pipeline"].step("process")

    bench_dict["my_pipeline"].gstop()

bench_dict.save()  # writes JSON files to PORTER_BENCH_PERFORMANCE/<timestamp>/
```

## Usage

### Pipeline benchmarking

`bench_dict["name"]` lazily creates a `Benchmarker`. The `gstep`/`gstop` pair marks iteration boundaries; `step(topic)` records time for a named sub-step within that iteration.

```python
from porter_bench import bench_dict

bench = bench_dict["pipeline"]
bench.set_save_on_gstop(4)  # auto-save every 4 iterations

for _ in range(20):
    bench.gstep()
    bench.step("load")
    bench.step("compute")
    bench.step("postprocess")
    bench.gstop()

bench_dict.save()
```

### Training loop with IterBench

`IterBench` wraps any iterable and calls `gstep()`/`gstop()` automatically around each iteration:

```python
from porter_bench import bench_dict
from porter_bench.GlobalBenchmarker import IterBench

for batch in IterBench(dataloader, bench_dict, "training"):
    bench_dict["training"].step("forward")
    bench_dict["training"].step("backward")
```

### Memory tracking

```python
bench = bench_dict["memory"]
bench.enable_memory_tracking(per_step=True)          # RAM tracking per step
bench.memory_benchmaker.enable_max_memory(poll_time=0.05)  # peak RAM polling

# Optional CUDA tracking (requires torch with CUDA)
bench.memory_benchmaker.enable_cuda_memory_tracking()
```

### Low-level timer utilities

```python
from porter_bench import timer
from porter_bench.basic import CountDownClock, TimedCounter

# Simple timer
timer.tic()
result = do_work()
elapsed = timer.toc()          # seconds since tic
elapsed = timer.ttoc()         # toc + reset

# Countdown
clock = CountDownClock(count_down_time=4.0)
while not clock.completed():
    print("time left:", clock.time_left())

# Frequency counter
counter = TimedCounter()
counter.start()
for _ in range(100):
    do_work()
    counter.count()
counter.stop()
print("frequency:", counter.get_frequency(), "Hz")
```

### Auto-save options

```python
bench.set_save_on_gstop(N)   # save every N iterations
bench.set_save_on_step(True)  # save after every step
```

## Loading and visualising results

```python
from porter_bench.utils import load_record
from porter_bench.DataHandler import DataHandler

record = load_record(".")          # loads latest run from PORTER_BENCH_PERFORMANCE/
handler = DataHandler({"run": record})

handler.plot_times(record_name="pipeline")
handler.make_bars(record_name="pipeline")
handler.plot_crono(record_name="pipeline")
handler.plot_memory_usage(record_name="memory")
```

Or use the `porter-bench-plots` CLI (installed with the package):

```bash
# Plot the latest run in the current directory
porter-bench-plots

# Specify search path and output directory
porter-bench-plots --path /path/to/project --output PLOTS

# Plot only specific benchmarker topics
porter-bench-plots --topics pipeline training

# Show plots interactively in addition to saving
porter-bench-plots --show

# Point directly at a specific record directory (skip auto-find)
porter-bench-plots --path PORTER_BENCH_PERFORMANCE/2024-01-01_12-00-00/run --no-latest
```

Or invoke as a module:

```bash
python -m porter_bench.plot_cli --path . --output PLOTS --show
```

| Flag | Default | Description |
|---|---|---|
| `--path PATH` | `.` | Root dir containing `PORTER_BENCH_PERFORMANCE/`, or a specific record dir with `--no-latest` |
| `--output DIR` | `PLOTS` | Directory to save generated plots |
| `--topics A B …` | all | Restrict to specific benchmarker names |
| `--show` | off | Display plots interactively in addition to saving |
| `--no-latest` | off | Treat `--path` as a specific record directory instead of auto-finding the latest run |

Plots are saved to `PLOTS/` as `<name>_times.png`, `<name>_bars.png`, `<name>_crono.png`, `<name>_memory.png`, and `<name>_cuda_memory.png` (if CUDA data is present).

## Output files

All JSON files are written under `PORTER_BENCH_PERFORMANCE/<timestamp>/<name>/`:

| File | Contents |
|---|---|
| `*_STEP_DICT_DATA.json` | Per-iteration step timings |
| `*_STEP_DICT_SUMMARY.json` | Aggregated mean/min/max stats |
| `*_MEMORY.json` | RAM and CUDA memory snapshots |

## Development

```bash
make test    # pytest
make lint    # pre-commit run --all-files
make example # run example.py then generate_plots.py
```

### PORTER_BENCH_TOGGLES

`PORTER_BENCH_TOGGLES` is an 8-bit binary string environment variable that exposes boolean feature flags for automating test variations without code changes. Each bit position is an independent toggle (index 0 = rightmost bit).

```bash
PORTER_BENCH_TOGGLES="00000001" pytest   # toggle 0 on
PORTER_BENCH_TOGGLES="00000011" pytest   # toggles 0 and 1 on
PORTER_BENCH_TOGGLES="10000000" pytest   # toggle 7 on
```

Inside the library, `PORTER_BENCH_TOGGLES` is parsed into a `list[bool]` of length 8, importable as:

```python
from porter_bench import PORTER_BENCH_TOGGLES

if PORTER_BENCH_TOGGLES[0]:
    # behaviour variant A
else:
    # behaviour variant B
```

This lets you drive conditional code paths — alternative algorithms, stricter assertions, extra logging — purely from the environment, making it easy to test both branches in CI or a single `pytest` run.
