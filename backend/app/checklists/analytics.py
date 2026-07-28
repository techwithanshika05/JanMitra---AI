from collections import Counter

from app.checklists.enums import ChecklistStatus, StorageOrigin
from app.checklists.repository import ChecklistRepository
from app.checklists.schemas import ChecklistAnalytics


class ChecklistAnalyticsService:
    @staticmethod
    def summarize(
        repository: ChecklistRepository,
        *,
        active_storage_mode: StorageOrigin,
    ) -> ChecklistAnalytics:
        rows = list(repository.all_for_analytics())
        total = len(rows)
        completed = [row for row in rows if row.progress_percentage >= 100]
        abandoned = [
            row
            for row in rows
            if row.is_archived and row.progress_percentage < 100
        ]
        completion_hours = []
        for row in completed:
            completed_times = [
                item.completed_at for item in row.items if item.completed_at is not None
            ]
            completion_time = max(completed_times) if completed_times else row.updated_at
            completion_hours.append(
                max(0.0, (completion_time - row.created_at).total_seconds() / 3600)
            )

        service_counts = Counter(
            (row.service_id, row.service_name) for row in rows
        )
        incomplete_counts = Counter(
            item.title
            for row in rows
            if not row.is_archived
            for item in row.items
            if item.is_required and not item.is_completed
        )
        storage_counts = Counter(row.storage_origin for row in rows)

        return ChecklistAnalytics(
            active_storage_mode=active_storage_mode,
            total_checklists=total,
            completion_rate=round(len(completed) / total, 4) if total else 0.0,
            abandonment_rate=round(len(abandoned) / total, 4) if total else 0.0,
            average_completion_hours=(
                round(sum(completion_hours) / len(completion_hours), 2)
                if completion_hours
                else 0.0
            ),
            outdated_count=sum(
                1 for row in rows if row.status == ChecklistStatus.OUTDATED.value
            ),
            most_saved_checklists=[
                {
                    "service_id": service_id,
                    "service_name": service_name,
                    "count": count,
                }
                for (service_id, service_name), count in service_counts.most_common(10)
            ],
            frequently_incomplete_steps=[
                {"title": title, "count": count}
                for title, count in incomplete_counts.most_common(10)
            ],
            storage_usage={
                StorageOrigin.POSTGRESQL.value: storage_counts[
                    StorageOrigin.POSTGRESQL.value
                ],
                StorageOrigin.SQLITE.value: storage_counts[
                    StorageOrigin.SQLITE.value
                ],
            },
        )
