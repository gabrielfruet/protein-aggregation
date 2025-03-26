import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
from functools import partial
from io import StringIO
from pathlib import Path
from threading import Lock, Thread
from typing import Set, Union

import duckdb
import pandas as pd
from Bio.PDB.PDBList import PDBList
from rich.console import Console, Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.theme import Theme

from src.protein.thermostability.coarse_grained import calculate_coarse_grained_metrics

NUMBER_OF_LOGS = 20
NUMBER_OF_THREADS = 16


def load_and_process_df_ddg():
    fireprot_df = pd.read_csv("./data/fireprotdb_results.csv")

    pdbid_ddg = duckdb.sql("""
    SELECT
        TRIM(s.value) AS pdb_id,
        ddG
    FROM 
        fireprot_df AS t,
        unnest(regexp_split_to_array(t.pdb_id, '\|')) AS s(value)
    WHERE 
        TRIM(s.value) != ''
        AND t.ddG IS NOT NULL
    """).df()

    return duckdb.sql("""
    SELECT pdb_id, AVG(ddG) as avg_ddG
    FROM pdbid_ddg
    GROUP BY pdb_id;
    """).df()


pdbid_avg_ddg = load_and_process_df_ddg()

pdblist = PDBList()
unique_pdb_ids: Set[str] = set(pdbid_avg_ddg["pdb_id"].unique())

unique_pdb_ids_lock = Lock()
live_render_lock = Lock()
logs_lock = Lock()
stdout_buffer = StringIO()

custom_theme = Theme({"progress.percentage": "orange1", "bar.complete": "white"})

console = Console(theme=custom_theme)
progress = Progress(
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TaskProgressColumn(style="blue"),
    TimeRemainingColumn(),
)
cache_path = Path("~/.cache/fireprot_db").expanduser()

if not cache_path.exists():
    console.log(f"[bright_yellow]Creating {cache_path}")
    cache_path.mkdir(parents=True, exist_ok=True)

number_of_pdbs_ids = len(unique_pdb_ids)
download_task = progress.add_task("Downloading PDB ids", total=number_of_pdbs_ids)


def download_pdb(pdb_id):
    """Download a PDB file to the cache directory."""
    with redirect_stderr(stdout_buffer):
        with redirect_stdout(stdout_buffer):
            pdblist.retrieve_pdb_file(
                pdb_id, pdir=cache_path.expanduser(), file_format="pdb"
            )


def get_and_download_pdb():
    """Worker function for downloading PDBs."""
    while True:
        with unique_pdb_ids_lock:
            if not unique_pdb_ids:
                break
            pdb_id = unique_pdb_ids.pop()

        stdout_buffer.flush()
        console.log(f"Downloading {pdb_id}")
        download_pdb(pdb_id)
        update_progress()


def update_progress():
    with live_render_lock:
        progress.advance(download_task)


def live_render():
    """Render function to update Live display."""
    with live_render_lock:
        return Group(
            progress,
        )


threads = [
    Thread(target=get_and_download_pdb, daemon=True) for _ in range(NUMBER_OF_THREADS)
]


def live_thread():
    """Run live rendering in a separate thread."""
    global threads
    with Live(live_render(), console=console, refresh_per_second=5) as live:
        while any(t.is_alive() for t in threads):
            live.update(live_render())
            time.sleep(0.2)  # Small delay to avoid excessive CPU usage


# Start the live rendering in a separate thread
live_display_thread = Thread(target=live_thread, daemon=False)
live_display_thread.start()

# Start worker threads
for t in threads:
    t.start()

# Wait for all threads to finish
for t in threads:
    t.join()

live_display_thread.join()

# Ensure live display stops once all work is done
console.print("[bold green]Download completed![/bold green]")

# %%


def path_given_pdbid(pdb_id: str):
    return cache_path / f"pdb{pdb_id.lower()}.ent"


def get_metrics(ent_path: Union[str, Path]):
    ent_path = Path(ent_path)
    pdb_path = ent_path.with_suffix(".pdb")
    shutil.copy(ent_path, pdb_path)
    return calculate_coarse_grained_metrics(pdb_path)


pdbid_avg_ddg["ent_path"] = pdbid_avg_ddg["pdb_id"].map(path_given_pdbid)

metrics = []

console = Console(theme=custom_theme)


def metric_worker(args, task, progress):
    ent_path, ddG = args
    try:
        console.log(f"Working on {ent_path}")
        metric = get_metrics(ent_path)
        metric["ddG"] = ddG
        progress.advance(task)
        return metric
    except Exception as e:
        console.log(f"Error {e}")
        progress.advance(task)
        return None


with Progress(console=console) as progress:
    task = progress.add_task(
        "Calculating coarse grained metrics for PDBs",
        total=len(pdbid_avg_ddg["ent_path"]),
    )
    with ThreadPoolExecutor(16) as executor:
        metrics_with_nones = executor.map(
            partial(metric_worker, task=task, progress=progress),
            zip(pdbid_avg_ddg["ent_path"], pdbid_avg_ddg["avg_ddG"]),
        )

metrics = list(filter(lambda x: x is not None, metrics_with_nones))
metrics_df = pd.DataFrame(metrics)

metrics_df.to_csv("data/coarse_grained_metrics_dgg.csv")
