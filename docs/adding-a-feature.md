# Adding a feature

1. **Pick the module** (`accounts`, `catalog`, `generation`, `dashboard`, `audit`). If it is
   genuinely cross-cutting, it belongs in `shared/` — otherwise it does not.
2. **Model / migration** (if needed) in `reports/models.py`; run
   `python manage.py makemigrations` and review the SQL. Never rename tables implicitly.
3. **Domain rules** (validation, state) in the module's `domain.py`/validation module.
4. **Use case** in `application.py` — orchestrate domain + ORM/infra, own transactions and
   any Celery enqueue (`transaction.on_commit`).
5. **Reads** in `selectors.py` (return querysets/dicts; no side effects).
6. **API**: `serializers.py` (shape only) + `views.py` (call the use case/selector, serialize).
7. **Tests** in `reports/tests/` — a characterization test first if you touch existing behavior.
8. Run the full "definition of done" checklist (see `CLAUDE.md`).

## Worked example — "cancel a report" use case

```python
# reports/generation/application.py
class CancelReportUseCase:
    def execute(self, *, report):
        from .domain import transition
        transition(report, report.Status.CANCELLED)  # raises if not allowed
        return report
```

```python
# reports/generation/views.py  (inside GeneratedReportViewSet)
@action(detail=True, methods=["post"], url_path="cancel")
def cancel(self, request, pk=None):
    report = CancelReportUseCase().execute(report=self.get_object())
    return Response(GeneratedReportStatusSerializer(report, context={"request": request}).data)
```

Add allowed transitions in `domain.py`, an audit action, and tests (allowed + forbidden cases).
