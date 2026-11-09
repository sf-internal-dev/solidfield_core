from django.core.management.base import BaseCommand, CommandError

from backend.apps.checklist.defaults.pesca_diario_operacional import (
    TEMPLATE_NAME,
    ensure_pesca_diario_operacional_template,
)
from backend.apps.core.models.tenant import CompanyTenant
from backend.apps.core.models.technician import Technician


class Command(BaseCommand):
    help = (
        "Creates the versioned checklist template "
        "'Daily Operational Log — Industrial Fishing' (diesel, ice, temperature) for a tenant."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant-id",
            type=int,
            default=None,
            help="CompanyTenant ID. If omitted, uses the first active tenant.",
        )
        parser.add_argument(
            "--technician-id",
            type=int,
            default=None,
            help="Technician ID (created_by). If omitted, uses the tenant's first active technician.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only reports whether the template would be created; does not write to the database.",
        )

    def handle(self, *args, **options):
        tenant_id = options["tenant_id"]
        technician_id = options["technician_id"]
        dry_run = options["dry_run"]

        if tenant_id is not None:
            try:
                tenant = CompanyTenant.objects.get(pk=tenant_id, is_active=True)
            except CompanyTenant.DoesNotExist as exc:
                raise CommandError(f"Tenant id={tenant_id} not found or inactive.") from exc
        else:
            tenant = CompanyTenant.objects.filter(is_active=True).order_by("id").first()
            if not tenant:
                raise CommandError(
                    "No active tenant found. Create a tenant or pass --tenant-id."
                )

        if technician_id is not None:
            try:
                technician = Technician.objects.get(
                    pk=technician_id,
                    tenant=tenant,
                    is_active=True,
                )
            except Technician.DoesNotExist as exc:
                raise CommandError(
                    f"Technician id={technician_id} not found, inactive, or from another tenant."
                ) from exc
        else:
            technician = (
                Technician.objects.filter(tenant=tenant, is_active=True).order_by("id").first()
            )
            if not technician:
                raise CommandError(
                    f"No active technician for tenant id={tenant.id}. "
                    "Register a technician or pass --technician-id."
                )

        template, status = ensure_pesca_diario_operacional_template(
            tenant,
            technician,
            dry_run=dry_run,
        )

        if status == "skipped":
            self.stdout.write(
                self.style.WARNING(
                    f"Template already exists: {TEMPLATE_NAME!r} v1 (tenant_id={tenant.id}). Nothing changed."
                )
            )
            return

        if status == "would_create":
            self.stdout.write(
                self.style.SUCCESS(
                    f"[dry-run] Would create template {TEMPLATE_NAME!r} v1 "
                    f"with 7 items (tenant_id={tenant.id}, created_by technician_id={technician.id})."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Created template id={template.id} {TEMPLATE_NAME!r} v1 "
                f"(tenant_id={tenant.id}, service_type=pesca_industrial_diario)."
            )
        )
