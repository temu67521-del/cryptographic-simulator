"""Pure Python implementations of 5 classical cryptographic algorithms with visual state traces."""

from __future__ import annotations

import math
import string
from typing import Any


ALPHABET = string.ascii_uppercase


class CipherValidationError(ValueError):
    """Raised when cipher input or key parameters are invalid."""


def _validate_non_empty_text(text: str, label: str = "Input text") -> str:
    if not isinstance(text, str) or not text.strip():
        raise CipherValidationError(f"{label} must not be empty.")
    return text


def _parse_int_key(key: Any, minimum: int, maximum: int, name: str) -> int:
    try:
        value = int(key)
    except (TypeError, ValueError) as exc:
        raise CipherValidationError(f"{name} must be an integer between {minimum} and {maximum}.") from exc
    if value < minimum or value > maximum:
        raise CipherValidationError(f"{name} must be between {minimum} and {maximum}.")
    return value


def _extract_alpha_key(key: Any, min_len: int = 1, name: str = "Keyword") -> str:
    if not isinstance(key, str):
        raise CipherValidationError(f"{name} must be a string.")
    cleaned = "".join(ch for ch in key.upper() if "A" <= ch <= "Z")
    if len(cleaned) < min_len:
        raise CipherValidationError(f"{name} must contain at least {min_len} alphabetic character(s).")
    return cleaned


# ---------------------------------------------------------------------------
# 1. Caesar Cipher
# ---------------------------------------------------------------------------

def caesar_transform(
    text: str,
    key: Any,
    mode: str = "encrypt",
    include_trace: bool = True,
) -> dict[str, Any]:
    """Encrypt or decrypt text using the Caesar cipher (shift 0-25)."""
    _validate_non_empty_text(text)
    shift = _parse_int_key(key, 0, 25, "Caesar shift")
    effective_shift = shift if mode == "encrypt" else (26 - shift) % 26

    out_chars: list[str] = []
    steps: list[dict[str, Any]] = []

    for idx, ch in enumerate(text):
        if "A" <= ch <= "Z":
            mapped = chr((ord(ch) - 65 + effective_shift) % 26 + 65)
            out_chars.append(mapped)
            if include_trace:
                steps.append({
                    "index": idx,
                    "input_char": ch,
                    "output_char": mapped,
                    "is_alpha": True,
                })
        elif "a" <= ch <= "z":
            mapped = chr((ord(ch) - 97 + effective_shift) % 26 + 97)
            out_chars.append(mapped)
            if include_trace:
                steps.append({
                    "index": idx,
                    "input_char": ch,
                    "output_char": mapped,
                    "is_alpha": True,
                })
        else:
            out_chars.append(ch)
            if include_trace:
                steps.append({
                    "index": idx,
                    "input_char": ch,
                    "output_char": ch,
                    "is_alpha": False,
                })

    result = "".join(out_chars)
    trace: dict[str, Any] = {}
    if include_trace:
        plain_alphabet = list(ALPHABET)
        shifted_alphabet = [ALPHABET[(i + shift) % 26] for i in range(26)]
        trace = {
            "algorithm": "caesar",
            "mode": mode,
            "shift": shift,
            "plain_alphabet": plain_alphabet,
            "shifted_alphabet": shifted_alphabet,
            "steps": steps[:120],
        }
    return {"output": result, "trace": trace}


# ---------------------------------------------------------------------------
# 2. Playfair Cipher
# ---------------------------------------------------------------------------

def _build_playfair_matrix(keyword: str) -> tuple[list[list[str]], dict[str, tuple[int, int]]]:
    cleaned = _extract_alpha_key(keyword, min_len=1, name="Playfair keyword").replace("J", "I")
    seen: set[str] = set()
    ordered: list[str] = []

    for ch in cleaned + "ABCDEFGHIKLMNOPQRSTUVWXYZ":
        if ch not in seen:
            seen.add(ch)
            ordered.append(ch)

    matrix: list[list[str]] = []
    positions: dict[str, tuple[int, int]] = {}
    for r in range(5):
        row: list[str] = []
        for c in range(5):
            letter = ordered[r * 5 + c]
            positions[letter] = (r, c)
            row.append("I/J" if letter == "I" else letter)
        matrix.append(row)

    positions["J"] = positions["I"]
    return matrix, positions


def _prepare_playfair_digraphs(text: str, mode: str) -> list[tuple[str, str]]:
    alpha = "".join(ch for ch in text.upper() if "A" <= ch <= "Z").replace("J", "I")
    if not alpha:
        raise CipherValidationError("Playfair input must contain at least one alphabetic character.")

    if mode == "decrypt":
        if len(alpha) % 2 != 0:
            raise CipherValidationError("Playfair ciphertext must have an even number of letters.")
        return [(alpha[i], alpha[i + 1]) for i in range(0, len(alpha), 2)]

    pairs: list[tuple[str, str]] = []
    i = 0
    while i < len(alpha):
        first = alpha[i]
        if i + 1 < len(alpha):
            second = alpha[i + 1]
            if first == second:
                filler = "Q" if first == "X" else "X"
                pairs.append((first, filler))
                i += 1
            else:
                pairs.append((first, second))
                i += 2
        else:
            filler = "Q" if first == "X" else "X"
            pairs.append((first, filler))
            i += 1
    return pairs


def playfair_transform(
    text: str,
    key: Any,
    mode: str = "encrypt",
    include_trace: bool = True,
) -> dict[str, Any]:
    """Encrypt or decrypt text using the 5x5 Playfair cipher (merging I/J)."""
    _validate_non_empty_text(text)
    matrix, positions = _build_playfair_matrix(key)
    digraphs = _prepare_playfair_digraphs(text, mode)
    delta = 1 if mode == "encrypt" else -1

    # Lookup table from (row, col) to single canonical letter ('I' for I/J)
    grid_letter = [
        ["I" if cell == "I/J" else cell for cell in row]
        for row in matrix
    ]

    output_pairs: list[str] = []
    trace_digraphs: list[dict[str, Any]] = []

    for a, b in digraphs:
        r1, c1 = positions[a]
        r2, c2 = positions[b]

        if r1 == r2:
            rule = "same-row"
            nr1, nc1 = r1, (c1 + delta) % 5
            nr2, nc2 = r2, (c2 + delta) % 5
        elif c1 == c2:
            rule = "same-col"
            nr1, nc1 = (r1 + delta) % 5, c1
            nr2, nc2 = (r2 + delta) % 5, c2
        else:
            rule = "rectangle"
            nr1, nc1 = r1, c2
            nr2, nc2 = r2, c1

        out_a = grid_letter[nr1][nc1]
        out_b = grid_letter[nr2][nc2]
        output_pairs.append(out_a + out_b)

        if include_trace:
            trace_digraphs.append({
                "pair": a + b,
                "result": out_a + out_b,
                "rule": rule,
                "coords": [[r1, c1], [r2, c2]],
                "result_coords": [[nr1, nc1], [nr2, nc2]],
            })

    result = "".join(output_pairs)
    trace: dict[str, Any] = {}
    if include_trace:
        trace = {
            "algorithm": "playfair",
            "mode": mode,
            "matrix": matrix,
            "digraphs": trace_digraphs[:80],
        }
    return {"output": result, "trace": trace}


# ---------------------------------------------------------------------------
# 3. Vigenère Cipher
# ---------------------------------------------------------------------------

def vigenere_transform(
    text: str,
    key: Any,
    mode: str = "encrypt",
    include_trace: bool = True,
) -> dict[str, Any]:
    """Encrypt or decrypt text using the Vigenère polyalphabetic cipher."""
    _validate_non_empty_text(text)
    keyword = _extract_alpha_key(key, min_len=1, name="Vigenère keyword")
    key_len = len(keyword)

    out_chars: list[str] = []
    plain_arr: list[str] = []
    key_arr: list[str] = []
    cipher_arr: list[str] = []
    steps: list[dict[str, Any]] = []

    key_idx = 0
    for idx, ch in enumerate(text):
        if "A" <= ch <= "Z" or "a" <= ch <= "z":
            k_char = keyword[key_idx % key_len]
            shift = ord(k_char) - 65
            key_idx += 1

            base = 65 if "A" <= ch <= "Z" else 97
            offset = ord(ch) - base
            if mode == "encrypt":
                mapped = chr((offset + shift) % 26 + base)
            else:
                mapped = chr((offset - shift) % 26 + base)

            out_chars.append(mapped)
            if include_trace and len(steps) < 120:
                plain_arr.append(ch)
                key_arr.append(k_char)
                cipher_arr.append(mapped)
                steps.append({
                    "index": idx,
                    "input_char": ch,
                    "key_char": k_char,
                    "shift": shift,
                    "output_char": mapped,
                    "is_alpha": True,
                })
        else:
            out_chars.append(ch)
            if include_trace and len(steps) < 120:
                plain_arr.append(ch)
                key_arr.append("·")
                cipher_arr.append(ch)
                steps.append({
                    "index": idx,
                    "input_char": ch,
                    "key_char": "·",
                    "shift": 0,
                    "output_char": ch,
                    "is_alpha": False,
                })

    result = "".join(out_chars)
    trace: dict[str, Any] = {}
    if include_trace:
        trace = {
            "algorithm": "vigenere",
            "mode": mode,
            "keyword": keyword,
            "plaintext_chars": plain_arr,
            "keystream_chars": key_arr,
            "ciphertext_chars": cipher_arr,
            "steps": steps,
        }
    return {"output": result, "trace": trace}


# ---------------------------------------------------------------------------
# 4. Rail Fence Cipher
# ---------------------------------------------------------------------------

def _rail_pattern(length: int, rails: int) -> list[int]:
    pattern: list[int] = []
    rail = 0
    direction = 1
    for _ in range(length):
        pattern.append(rail)
        if rail == 0:
            direction = 1
        elif rail == rails - 1:
            direction = -1
        rail += direction
    return pattern


def rail_fence_transform(
    text: str,
    key: Any,
    mode: str = "encrypt",
    include_trace: bool = True,
) -> dict[str, Any]:
    """Encrypt or decrypt text using the Rail Fence zig-zag cipher (2-10 rails)."""
    _validate_non_empty_text(text)
    rails = _parse_int_key(key, 2, 10, "Rail depth")
    n = len(text)
    pattern = _rail_pattern(n, rails)

    if mode == "encrypt":
        rail_buckets: list[list[str]] = [[] for _ in range(rails)]
        for ch, r in zip(text, pattern):
            rail_buckets[r].append(ch)
        result = "".join("".join(bucket) for bucket in rail_buckets)
        char_sequence = list(text)
    else:
        counts = [0] * rails
        for r in pattern:
            counts[r] += 1

        rail_slices: list[list[str]] = []
        pos = 0
        for count in counts:
            rail_slices.append(list(text[pos : pos + count]))
            pos += count

        rail_cursors = [0] * rails
        decoded: list[str] = []
        for r in pattern:
            decoded.append(rail_slices[r][rail_cursors[r]])
            rail_cursors[r] += 1
        result = "".join(decoded)
        char_sequence = decoded

    trace: dict[str, Any] = {}
    if include_trace:
        vis_len = min(n, 64)
        matrix: list[list[str | None]] = [[None for _ in range(vis_len)] for _ in range(rails)]
        path: list[dict[str, Any]] = []
        for idx in range(vis_len):
            r = pattern[idx]
            ch = char_sequence[idx]
            matrix[r][idx] = ch
            path.append({"index": idx, "rail": r, "char": ch})

        rail_strings = ["".join(c for c in row if c is not None) for row in matrix]
        trace = {
            "algorithm": "rail_fence",
            "mode": mode,
            "rails": rails,
            "length": vis_len,
            "total_length": n,
            "matrix": matrix,
            "path": path,
            "rail_strings": rail_strings,
        }
    return {"output": result, "trace": trace}


# ---------------------------------------------------------------------------
# 5. Columnar Transposition Cipher
# ---------------------------------------------------------------------------

def columnar_transform(
    text: str,
    key: Any,
    mode: str = "encrypt",
    include_trace: bool = True,
) -> dict[str, Any]:
    """Encrypt or decrypt text using Columnar Transposition with 'X' padding."""
    _validate_non_empty_text(text)
    keyword = _extract_alpha_key(key, min_len=2, name="Columnar keyword")
    num_cols = len(keyword)

    # Determine column readout order (alphabetical sort, stable on original index)
    read_order = [idx for idx, _ in sorted(enumerate(keyword), key=lambda item: (item[1], item[0]))]
    ranks = [0] * num_cols
    for rank_idx, col_idx in enumerate(read_order, start=1):
        ranks[col_idx] = rank_idx

    if mode == "encrypt":
        num_rows = math.ceil(len(text) / num_cols)
        padded_len = num_rows * num_cols
        padded_text = text.ljust(padded_len, "X")
        grid = [
            list(padded_text[r * num_cols : (r + 1) * num_cols])
            for r in range(num_rows)
        ]
        out_chunks: list[str] = []
        readout_sequence: list[dict[str, Any]] = []
        for col_idx in read_order:
            col_chars = [grid[r][col_idx] for r in range(num_rows)]
            out_chunks.append("".join(col_chars))
            if include_trace:
                readout_sequence.append({
                    "col": col_idx,
                    "letter": keyword[col_idx],
                    "rank": ranks[col_idx],
                    "chars": col_chars[:20],
                })
        result = "".join(out_chunks)
    else:
        num_rows = math.ceil(len(text) / num_cols)
        padded_len = num_rows * num_cols
        padded_text = text.ljust(padded_len, "X")
        grid = [["" for _ in range(num_cols)] for _ in range(num_rows)]

        pos = 0
        readout_sequence = []
        for col_idx in read_order:
            col_chars: list[str] = []
            for r in range(num_rows):
                ch = padded_text[pos]
                grid[r][col_idx] = ch
                col_chars.append(ch)
                pos += 1
            if include_trace:
                readout_sequence.append({
                    "col": col_idx,
                    "letter": keyword[col_idx],
                    "rank": ranks[col_idx],
                    "chars": col_chars[:20],
                })
        result = "".join("".join(row) for row in grid)

    trace: dict[str, Any] = {}
    if include_trace:
        trace = {
            "algorithm": "columnar",
            "mode": mode,
            "keyword": keyword,
            "ranks": ranks,
            "read_order": read_order,
            "grid": grid[:16],
            "readout_sequence": readout_sequence,
        }
    return {"output": result, "trace": trace}


# ---------------------------------------------------------------------------
# Unified Dispatcher
# ---------------------------------------------------------------------------

CIPHER_REGISTRY = {
    "caesar": caesar_transform,
    "playfair": playfair_transform,
    "vigenere": vigenere_transform,
    "rail_fence": rail_fence_transform,
    "columnar": columnar_transform,
}


def run_cipher(
    algorithm: str,
    text: str,
    key: Any,
    mode: str = "encrypt",
    include_trace: bool = True,
) -> dict[str, Any]:
    """Execute any supported cipher with validation and optional visual trace."""
    algo_key = algorithm.strip().lower()
    if algo_key not in CIPHER_REGISTRY:
        raise CipherValidationError(f"Unsupported algorithm: {algorithm}")
    if mode not in ("encrypt", "decrypt"):
        raise CipherValidationError("Mode must be 'encrypt' or 'decrypt'.")
    return CIPHER_REGISTRY[algo_key](text=text, key=key, mode=mode, include_trace=include_trace)
