"""CLI and helper functions for generating plots from porter_bench records."""

import argparse
import os
from typing import Any, List, Optional

import matplotlib.pyplot as plt

from .DataHandler import DataHandler
from .utils import load_record


def get_record_names(record: dict[str, Any]) -> list[str]:
    """Return the benchmarker names present in the loaded record."""
    return list(record["absolutes"].keys())


def generate_plots(
    record_path: str = ".",
    output_dir: str = "PLOTS",
    topics: Optional[List[str]] = None,
    show: bool = False,
    only_latest: bool = True,
) -> None:
    """Load benchmark records and generate all plots, saving them to output_dir.

    Args:
        record_path: Root directory containing PORTER_BENCH_PERFORMANCE/ when
            only_latest=True, or a specific record directory when only_latest=False.
        output_dir: Directory to save generated plots. Defaults to 'PLOTS'.
        topics: Benchmarker names to plot. Defaults to all found in the record.
        show: Whether to display plots interactively in addition to saving.
        only_latest: If True, auto-find the latest run under PORTER_BENCH_PERFORMANCE/.
            If False, treat record_path as a specific record directory.
    """
    print(f"Loading record from: {os.path.abspath(record_path)}")
    record = load_record(record_path, only_latest=only_latest)

    record_names = get_record_names(record)
    if topics is not None:
        missing = [t for t in topics if t not in record_names]
        if missing:
            print(f"Warning: topics not found in record: {missing}")
        record_names = [n for n in record_names if n in topics]

    print(f"Plotting benchmarkers: {record_names}")
    os.makedirs(output_dir, exist_ok=True)

    # DataHandler expects {run_label: record} — one entry per run being compared
    handler = DataHandler({"run": record})

    for record_name in record_names:
        print(f"\n--- Plotting '{record_name}' ---")

        # 1. Time series (absolutes per iteration)
        plt.figure(figsize=(14, 5))
        plt.title(f"{record_name} — time series")
        handler.plot_times(record_name=record_name)
        plt.tight_layout()
        out = os.path.join(output_dir, f"{record_name}_times.png")
        plt.savefig(out, dpi=150)
        print(f"  Saved: {out}")
        if show:
            plt.show()
        plt.close()

        # 2. Bar charts (mean / quantile-filtered mean per step)
        handler.make_bars(record_name=record_name)
        out = os.path.join(output_dir, f"{record_name}_bars.png")
        plt.savefig(out, dpi=150)
        print(f"  Saved: {out}")
        if show:
            plt.show()
        plt.close()

        # 3. Chronological call plot
        plt.figure(figsize=(16, 5))
        plt.title(f"{record_name} — chronological calls")
        handler.plot_crono(record_name=record_name)
        plt.tight_layout()
        out = os.path.join(output_dir, f"{record_name}_crono.png")
        plt.savefig(out, dpi=150)
        print(f"  Saved: {out}")
        if show:
            plt.show()
        plt.close()

        # 4. Memory usage (only if memory data is present)
        mem_data = record["memory"].get(record_name)
        if mem_data and len(mem_data) > 0:
            plt.figure(figsize=(16, 5))
            handler.plot_memory_usage(record_name=record_name)
            plt.tight_layout()
            out = os.path.join(output_dir, f"{record_name}_memory.png")
            plt.savefig(out, dpi=150)
            print(f"  Saved: {out}")
            if show:
                plt.show()
            plt.close()

            # 5. CUDA memory usage (skipped silently if no CUDA data)
            plt.figure(figsize=(16, 5))
            handler.plot_cuda_memory(record_name=record_name)
            if plt.gca().has_data():
                plt.tight_layout()
                out = os.path.join(output_dir, f"{record_name}_cuda_memory.png")
                plt.savefig(out, dpi=150)
                print(f"  Saved: {out}")
                if show:
                    plt.show()
            else:
                print("  Skipping CUDA memory plot (no CUDA data)")
            plt.close()
        else:
            print("  Skipping memory plots (no memory data)")

    print(f"\nAll plots saved to: {os.path.abspath(output_dir)}/")


def main() -> None:
    """Entry point for the porter-bench-plots CLI command."""
    parser = argparse.ArgumentParser(
        description="Generate all plots from porter_bench records.",
        prog="python -m porter_bench.plot_cli",
    )
    parser.add_argument(
        "--path",
        default=".",
        help=(
            "Root directory containing PORTER_BENCH_PERFORMANCE/ (default: current dir). "
            "Use --no-latest to treat this as a specific record directory instead."
        ),
    )
    parser.add_argument(
        "--output",
        default="PLOTS",
        help="Directory to save plots (default: PLOTS/)",
    )
    parser.add_argument(
        "--topics",
        nargs="+",
        default=None,
        help="Specific benchmarker topics to plot (default: all)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show plots interactively in addition to saving",
    )
    parser.add_argument(
        "--no-latest",
        dest="only_latest",
        action="store_false",
        default=True,
        help=(
            "Treat --path as a specific record directory instead of "
            "auto-finding the latest run under PORTER_BENCH_PERFORMANCE/"
        ),
    )
    args = parser.parse_args()
    generate_plots(
        record_path=args.path,
        output_dir=args.output,
        topics=args.topics,
        show=args.show,
        only_latest=args.only_latest,
    )


if __name__ == "__main__":
    main()
