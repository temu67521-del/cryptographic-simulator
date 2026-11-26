"""Micro-benchmarking and Shannon entropy analysis for classical ciphers."""

from __future__ import annotations

import math
import time
from collections import Counter
from typing import Any

from ciphers import run_cipher


PAYLOAD_SIZES: dict[str, int] = {
    "100 B": 100,
    "1 KB": 1024,
    "10 KB": 10240,
    "50 KB": 51200,
}

DEFAULT_BENCHMARK_KEYS: dict[str, Any] = {
    "caesar": 7,
    "playfair": "OBSIDIAN",
    "vigenere": "QUANTUM",
    "rail_fence": 4,
    "columnar": "CIPHER",
}

ALGORITHM_LABELS: dict[str, str] = {
    "caesar": "Caesar",
    "playfair": "Playfair",
    "vigenere": "Vigenère",
    "rail_fence": "Rail Fence",
    "columnar": "Columnar",
}

SAMPLE_SEED = (
    "CRYPTOGRAPHIC SYSTEMS SIMULATOR BENCHMARK PAYLOAD "
    "THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG "
    "SECURITY ENTROPY DIFFUSION CONFUSION PERMUTATION "
)


def calculate_shannon_entropy(text: str) -> float:
    """Compute Shannon entropy in bits per character."""
    if not text:
        return 0.0
    length = len(text)
    counts = Counter(text)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return round(entropy, 4)


def compute_frequency_distribution(text: str) -> dict[str, float]:
    """Compute normalized A-Z percentage frequency distribution."""
    letters = [ch for ch in text.upper() if "A" <= ch <= "Z"]
    total = len(letters)
    counts = Counter(letters)
    if total == 0:
        return {chr(code): 0.0 for code in range(65, 91)}
    return {
        chr(code): round((counts.get(chr(code), 0) / total) * 100.0, 2)
        for code in range(65, 91)
    }


def _build_payload(size_bytes: int) -> str:
    repeats = (size_bytes // len(SAMPLE_SEED)) + 1
    return (SAMPLE_SEED * repeats)[:size_bytes]


def run_benchmark_suite(
    runs: int = 20,
    custom_text: str | None = None,
    selected_algorithm: str = "vigenere",
    selected_key: Any = None,
) -> dict[str, Any]:
    """Benchmark all 5 algorithms across 100B, 1KB, 10KB, and 50KB payloads."""
    algorithms = list(DEFAULT_BENCHMARK_KEYS.keys())
    latency_ms: dict[str, list[float]] = {algo: [] for algo in algorithms}
    throughput_mbps: dict[str, list[float]] = {algo: [] for algo in algorithms}
    entropy_by_algo: dict[str, float] = {}

    for label, size_bytes in PAYLOAD_SIZES.items():
        payload = _build_payload(size_bytes)
        payload_mb = size_bytes / (1024.0 * 1024.0)

        for algo in algorithms:
            key = DEFAULT_BENCHMARK_KEYS[algo]
            start_ns = time.perf_counter_ns()
            last_output = ""
            for _ in range(runs):
                res = run_cipher(algo, payload, key, mode="encrypt", include_trace=False)
                last_output = res["output"]
            elapsed_ns = time.perf_counter_ns() - start_ns

            avg_ns = elapsed_ns / runs
            avg_ms = avg_ns / 1_000_000.0
            seconds = avg_ns / 1_000_000_000.0
            mbps = payload_mb / seconds if seconds > 0 else 0.0

            latency_ms[algo].append(round(avg_ms, 4))
            throughput_mbps[algo].append(round(mbps, 3))

            if label == "10 KB":
                entropy_by_algo[algo] = calculate_shannon_entropy(last_output)

    # Plaintext vs Ciphertext frequency and entropy comparison on 10 KB or user text
    sample_plain = custom_text.strip() if custom_text and custom_text.strip() else _build_payload(4096)
    target_algo = selected_algorithm if selected_algorithm in DEFAULT_BENCHMARK_KEYS else "vigenere"
    target_key = selected_key if selected_key not in (None, "") else DEFAULT_BENCHMARK_KEYS[target_algo]

    try:
        sample_cipher = run_cipher(target_algo, sample_plain, target_key, mode="encrypt", include_trace=False)["output"]
    except Exception:
        sample_cipher = run_cipher(
            target_algo,
            sample_plain,
            DEFAULT_BENCHMARK_KEYS[target_algo],
            mode="encrypt",
            include_trace=False,
        )["output"]

    return {
        "runs": runs,
        "payload_labels": list(PAYLOAD_SIZES.keys()),
        "algorithms": [
            {"id": algo, "label": ALGORITHM_LABELS[algo]}
            for algo in algorithms
        ],
        "latency_ms": latency_ms,
        "throughput_mbps": throughput_mbps,
        "entropy": {
            "plaintext": calculate_shannon_entropy(sample_plain),
            "ciphertext": calculate_shannon_entropy(sample_cipher),
            "by_algorithm_10kb": entropy_by_algo,
            "sample_algorithm": ALGORITHM_LABELS.get(target_algo, target_algo),
        },
        "frequency_distribution": {
            "labels": [chr(code) for code in range(65, 91)],
            "plaintext": compute_frequency_distribution(sample_plain),
            "ciphertext": compute_frequency_distribution(sample_cipher),
        },
    }
