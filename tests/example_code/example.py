import os
from collections.abc import Sequence
from datetime import timedelta
from pathlib import Path
from time import time
from typing import Callable, final

import numpy as np
import torch
import torch.distributed as dist
from giggleml.dataWrangling import fasta
from giggleml.dataWrangling.unifiedDataset import UnifiedDataset
from torch import multiprocessing as mp
from torch.utils.data import DataLoader

from ..dataWrangling.intervalDataset import IntervalDataset
from ..utils.guessDevice import guessDevice
from ..utils.types import GenomicInterval, ListLike
from .blockDistributedSampler import BlockDistributedSampler
from .embedModel import EmbedModel


@final
class FastaCollate:
    def __init__(self, fasta: str):
        self.fasta = fasta

    def __call__(self, batch: Sequence[GenomicInterval]):
        return fasta.map(batch, self.fasta)


def pass_collate(batch: Sequence[GenomicInterval]):
    return batch


@final
class BatchInfer:
    def __init__(
        self,
        model: EmbedModel,
        batch_size: int,
        worker_count: int,
        sub_worker_count: int,
    ):
        """
        @param workerCount: should be <= gpu count
        @param subWorkerCount: corresponds to pytorch::DataLoader::num_worker
        argument -- used to prepare subprocesses for batch construction. Can be
        zero.
        """
        if worker_count == 0:
            raise ValueError("No workers; no work.")
        self.model = model
        self.batch_size = batch_size
        self.worker_count = worker_count
        self.sub_worker_count = sub_worker_count
        self.embed_dim = model.embedDim

    def _infer_loop(self, rank: int, data_loader: DataLoader, out_file: np.memmap):
        """inference loop."""
        rprint = lambda *args: print(f"[{rank}]:", *args)
        time0 = time()
        next_idx = 0
        for i, batch in enumerate(data_loader):
            outputs = self.model.embed(batch).to("cpu")
            final_idx = next_idx + len(outputs)
            assert final_idx <= len(out_file)
            out_file[next_idx:final_idx] = outputs.detach().numpy()
            next_idx += len(outputs)
            if i % 50 == 0:
                rprint(f"Batch: {i + 1}\t/ {len(data_loader)}")
            if i % 150 == 1 and rank == 0:
                elapsed = time() - time0
                eta = timedelta(seconds=elapsed / (i + 1) * len(data_loader) - elapsed)
                elapsed_dt = timedelta(seconds=elapsed)
                rprint(f"== {str(elapsed_dt)}, ETA: {str(eta)}")
        rprint(f"Batch: {len(data_loader)}\t/ {len(data_loader)}")
        out_file.flush()
        del outFile

    def _worker(
        self,
        rank: int,
        datasets: Sequence[IntervalDataset],
        out_paths: Sequence[str],
        post: Sequence[Callable[[np.memmap], None]] | None,
    ):
        device = guessDevice(rank)
        if rank == 0:
            print("Starting inference.")
        rprint = lambda *args: print(f"[{rank}]:", *args)
        fasta: str | None = None
        for dataset in datasets:
            dataset_fasta = dataset.associatedFastaPath
            if fasta is None:
                fasta = dataset_fasta
            elif fasta != dataset_fasta:
                raise ValueError("Expecting all datasets to have same fasta path")
        master_dataset = UnifiedDataset[GenomicInterval](datasets)
        model = self.model.to(device)
        model.to(device)
        wants_seq = self.model.wants == "sequences"
        e_dim = self.model.embedDim
        if wants_seq:
            if fasta is None:
                raise ValueError("Unable to map to fasta; missing associatedFastaPath")
            collate = FastaCollate(fasta)
        else:
            collate = passCollate
        block_sampler = BlockDistributedSampler(master_dataset, self.worker_count, rank)
        sample_count = len(block_sampler)
        offset = block_sampler.lower * e_dim * 4
        master_out_path = Path(out_paths[0]).parent / "wip.tmp.npy"
        master_out_file = np.memmap(
            master_out_path, np.float32, "r+", offset, shape=(sample_count, e_dim)
        )
        data_loader = DataLoader(
            master_dataset,
            batch_size=self.batch_size,
            sampler=block_sampler,
            shuffle=False,
            pin_memory=True,
            num_workers=self.sub_worker_count,
            persistent_workers=self.sub_worker_count != 0,
            collate_fn=collate,
        )
        try:
            os.environ["MASTER_ADDR"] = "localhost"
            os.environ["MASTER_PORT"] = "12356"
            dist.init_process_group(
                backend="nccl" if torch.cuda.is_available() else "gloo",
                rank=rank,
                world_size=self.worker_count,
                timeout=timedelta(
                    seconds=len(master_dataset) / self.worker_count * 0.5
                ),
                device_id=device if device.type == "cuda" else None,
            )
            if not dist.is_initialized():
                raise RuntimeError("Process group could not initialized")
            dist.barrier()
            self._infer_loop(rank, data_loader, master_out_file)
            dist.barrier()
            if rank == 0:
                print("Starting post-processing.")
            set_idx_start = (
                master_dataset.listIdxOf(block_sampler.lower)
                if block_sampler.lower < len(master_dataset)
                else len(master_dataset.lists)
            )
            set_idx_end = (
                master_dataset.listIdxOf(block_sampler.upper)
                if block_sampler.upper < len(master_dataset)
                else len(master_dataset.lists)
            )
            master_out_file.flush()
            del masterOutFile
            master_size = (
                master_dataset.sums[set_idx_end] - master_dataset.sums[set_idx_start]
            )
            master_out_file = np.memmap(
                master_out_path,
                np.float32,
                "r",
                offset=master_dataset.sums[set_idx_start] * e_dim * 4,
                shape=(master_size, e_dim),
            )
            for set_idx in range(set_idx_start, set_idx_end):
                size = len(datasets[set_idx])
                out_path = out_paths[set_idx]
                i = master_dataset.sums[set_idx] - master_dataset.sums[set_idx_start]
                content = master_out_file[i : i + size]
                mmap = np.memmap(out_path, np.float32, "w+", shape=(size, e_dim))
                mmap[:] = content
                mmap.flush()
                if post is not None:
                    post_call = post[set_idx]
                    post_call(mmap)
                if rank == 0:
                    if 100 * set_idx // len(out_paths) % 10 == 0:
                        rprint(f"{set_idx + 1} / {len(out_paths)}")
            rprint(f"{len(out_paths)} / {len(out_paths)}")
            dist.barrier()
        finally:
            dist.destroy_process_group()

    def batch(
        self,
        datasets: Sequence[ListLike],
        out_paths: Sequence[str],
        post: Sequence[Callable[[np.memmap], None]] | None = None,
    ):
        """
        @param post: Is a list of processing Callable to apply to completed memmaps after inference is completed.
        """
        assert len(datasets) == len(out_paths)
        e_dim = self.model.embedDim
        total_len = sum([len(dataset) for dataset in datasets])
        master_out = Path(out_paths[0]).parent.mkdir(parents=True, exist_ok=True)
        master_out = Path(out_paths[0]).parent / "wip.tmp.npy"
        mm_total = np.memmap(master_out, np.float32, "w+", shape=(total_len, e_dim))
        mm_total[:] = 0
        mm_total.flush()
        del mmTotal
        args = (datasets, out_paths, post)
        mp.spawn(self._worker, args=args, nprocs=self.worker_count, join=True)
        os.remove(master_out)

