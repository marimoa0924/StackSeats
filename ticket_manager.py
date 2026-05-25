from __future__ import annotations

from stack import CancelTicketStack
from seat_config import ALL_GRADES


class TicketManager:
    def __init__(self) -> None:
        self._stacks: dict[str, CancelTicketStack] = {
            grade: CancelTicketStack() for grade in ALL_GRADES
        }

    def push(self, seat_data: dict) -> bool:
        """취소표를 해당 등급 스택 TOP에 삽입 (PUSH).

        seat_data 필드: seat_id, grade, seller_phone,
                        receipt_bytes, receipt_filename
        중복 seat_id가 이미 스택에 있으면 False 반환.
        """
        grade = seat_data.get("grade")
        if grade not in self._stacks:
            return False
        if seat_data["seat_id"] in self.get_all_cancelled_seats():
            return False
        self._stacks[grade].push(seat_data)
        return True

    def pop(self, grade: str) -> dict | None:
        """해당 등급 스택 TOP 취소표를 제거하고 반환 (POP)."""
        if grade not in self._stacks:
            return None
        return self._stacks[grade].pop()

    def peek(self, grade: str) -> dict | None:
        """해당 등급 스택 TOP 취소표를 제거 없이 조회 (PEEK)."""
        if grade not in self._stacks:
            return None
        return self._stacks[grade].peek()

    def get_stack_state(self, grade: str) -> list[dict]:
        """해당 등급 스택 전체를 리스트로 반환 (index 0=BOTTOM, -1=TOP)."""
        if grade not in self._stacks:
            return []
        return self._stacks[grade].to_list()

    def get_all_cancelled_seats(self) -> set[str]:
        """현재 모든 스택에 있는 seat_id 집합 반환."""
        result: set[str] = set()
        for grade in ALL_GRADES:
            for seat in self._stacks[grade].to_list():
                result.add(seat["seat_id"])
        return result

    def get_all_status(self) -> dict[str, list[dict]]:
        return {grade: self._stacks[grade].to_list() for grade in ALL_GRADES}

    def get_size(self, grade: str) -> int:
        if grade not in self._stacks:
            return 0
        return self._stacks[grade].size()

    def is_empty(self, grade: str) -> bool:
        if grade not in self._stacks:
            return True
        return self._stacks[grade].is_empty()

    def total_count(self) -> int:
        return sum(self._stacks[g].size() for g in ALL_GRADES)
