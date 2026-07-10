import hashlib
import difflib
from typing import Tuple, Dict, Any, Optional

class ByteComparator:
    @staticmethod
    def compute_sha256(content: str) -> str:
        if not content:
            return ""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def compare(self, patch_1: str, patch_2: str) -> Dict[str, Any]:
        """
        Compares two patches byte-for-byte.
        Generates a unified diff if there is a mismatch.
        """
        if patch_1 is None or patch_2 is None:
            return {
                "is_match": False,
                "diff": "One or both patch runs failed to generate.",
                "size_diff_bytes": 0,
                "run_1_hash": self.compute_sha256(patch_1 or ""),
                "run_2_hash": self.compute_sha256(patch_2 or "")
            }

        # Byte-level check
        bytes_1 = patch_1.encode("utf-8")
        bytes_2 = patch_2.encode("utf-8")

        is_match = (bytes_1 == bytes_2)
        run_1_hash = self.compute_sha256(patch_1)
        run_2_hash = self.compute_sha256(patch_2)
        size_diff = len(bytes_2) - len(bytes_1)

        diff_text = None
        if not is_match:
            # Generate diff using unified_diff
            lines_1 = patch_1.splitlines(keepends=True)
            lines_2 = patch_2.splitlines(keepends=True)
            diff_gen = difflib.unified_diff(
                lines_1, lines_2,
                fromfile='patch_run_1.py',
                tofile='patch_run_2.py'
            )
            diff_text = "".join(diff_gen)

        return {
            "is_match": is_match,
            "diff": diff_text,
            "size_diff_bytes": size_diff,
            "run_1_hash": run_1_hash,
            "run_2_hash": run_2_hash
        }
