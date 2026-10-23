"""Track distinct server observations, separately from transport heartbeats."""
from dataclasses import dataclass, field


@dataclass
class ProgressConfirmation:
    values: dict[str, float] = field(default_factory=dict)
    last_sync: float = 0
    last_growth: float = 0
    unchanged_polls: int = 0

    def observe(self, snapshot, *, running: bool) -> None:
        if snapshot.error or not snapshot.progresses or not getattr(snapshot, "server_confirmed", True):
            return
        if snapshot.refreshed_at <= self.last_sync:
            return
        values = {}
        for task in snapshot.progresses:
            for index, p in enumerate(task.check_points or [task]):
                key = f"{task.task_id}:{getattr(p, 'sid', '') or index}"
                values[key] = float(p.cur_value or 0)
        same_tasks = values.keys() == self.values.keys()
        if not same_tasks:
            self.last_growth = 0
        growth = same_tasks and any(v > self.values[k] for k, v in values.items())
        if growth:
            self.last_growth = snapshot.refreshed_at
        self.unchanged_polls = self.unchanged_polls + 1 if running and same_tasks and not growth else 0
        self.values = values
        self.last_sync = snapshot.refreshed_at

    def label(self, *, now: float, interval: int) -> str:
        if not self.last_sync:
            return "等待平台同步"
        age = max(0, int(now - self.last_sync))
        if age > max(90, interval * 3):
            return f"平台数据已过期 · {age} 秒未同步"
        if self.unchanged_polls >= 3:
            return f"平台进度连续 {self.unchanged_polls} 次未增长 · 同步 {age} 秒前"
        if self.last_growth:
            return f"平台确认进度增长 · {max(0, int(now - self.last_growth))} 秒前"
        return f"平台已同步 · {age} 秒前"
