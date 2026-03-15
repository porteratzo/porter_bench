"""Generate all plots from porter_bench records.

This script is a thin wrapper around ``porter_bench.plot_cli``.
You can also run the same CLI directly as a module::

    python -m porter_bench.plot_cli --path . --output PLOTS --show
"""

from porter_bench.plot_cli import generate_plots, get_record_names, main  # noqa: F401

if __name__ == "__main__":
    main()
