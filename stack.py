from __future__ import annotations


class CancelTicketStack:
    def __init__(self) -> None:
        self._stack: list[dict] = []

    def push(self, seat: dict) -> None:
        """취소표를 스택 최상단(TOP)에 삽입 — O(1)"""
        self._stack.append(seat)

    def pop(self) -> dict | None:
        """스택 최상단(TOP) 취소표를 제거하고 반환 — O(1)"""
        if self.is_empty():
            return None
        return self._stack.pop()

    def peek(self) -> dict | None:
        """스택 최상단(TOP) 취소표를 제거 없이 조회 — O(1)"""
        return self._stack[-1] if self._stack else None

    def is_empty(self) -> bool:
        return len(self._stack) == 0

    def size(self) -> int:
        return len(self._stack)

    def to_list(self) -> list[dict]:
        """내부 스택 상태를 복사본 리스트로 반환.
        인덱스 0 = BOTTOM(가장 오래된), 마지막 = TOP(가장 최신).
        """
        return list(self._stack)
