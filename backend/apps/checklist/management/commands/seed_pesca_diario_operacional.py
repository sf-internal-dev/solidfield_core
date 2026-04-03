from django.core.management.base import BaseCommand, CommandError

from backend.apps.checklist.defaults.pesca_diario_operacional import (
    TEMPLATE_NAME,
    ensure_pesca_diario_operacional_template,
)
from backend.apps.core.models.tenant import CompanyTenant
from backend.apps.core.models.technician import Technician


class Command(BaseCommand):
    help = (
        "Cria o checklist template versionado "
        "'Diário Operacional — Pesca Industrial' (diesel, gelo, temperatura) para um tenant."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant-id",
            type=int,
            default=None,
            help="ID do CompanyTenant. Se omitido, usa o primeiro tenant ativo.",
        )
        parser.add_argument(
            "--technician-id",
            type=int,
            default=None,
            help="ID do Technician (created_by). Se omitido, usa o primeiro técnico ativo do tenant.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Apenas indica se criaria o template; não grava no banco.",
        )

    def handle(self, *args, **options):
        tenant_id = options["tenant_id"]
        technician_id = options["technician_id"]
        dry_run = options["dry_run"]

        if tenant_id is not None:
            try:
                tenant = CompanyTenant.objects.get(pk=tenant_id, is_active=True)
            except CompanyTenant.DoesNotExist as exc:
                raise CommandError(f"Tenant id={tenant_id} não encontrado ou inativo.") from exc
        else:
            tenant = CompanyTenant.objects.filter(is_active=True).order_by("id").first()
            if not tenant:
                raise CommandError(
                    "Nenhum tenant ativo encontrado. Crie um tenant ou passe --tenant-id."
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
                    f"Técnico id={technician_id} não encontrado, inativo ou de outro tenant."
                ) from exc
        else:
            technician = (
                Technician.objects.filter(tenant=tenant, is_active=True).order_by("id").first()
            )
            if not technician:
                raise CommandError(
                    f"Nenhum técnico ativo para tenant id={tenant.id}. "
                    "Cadastre um técnico ou passe --technician-id."
                )

        template, status = ensure_pesca_diario_operacional_template(
            tenant,
            technician,
            dry_run=dry_run,
        )

        if status == "skipped":
            self.stdout.write(
                self.style.WARNING(
                    f"Template já existe: {TEMPLATE_NAME!r} v1 (tenant_id={tenant.id}). Nada alterado."
                )
            )
            return

        if status == "would_create":
            self.stdout.write(
                self.style.SUCCESS(
                    f"[dry-run] Seria criado template {TEMPLATE_NAME!r} v1 "
                    f"com 7 itens (tenant_id={tenant.id}, created_by technician_id={technician.id})."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Criado template id={template.id} {TEMPLATE_NAME!r} v1 "
                f"(tenant_id={tenant.id}, service_type=pesca_industrial_diario)."
            )
        )
