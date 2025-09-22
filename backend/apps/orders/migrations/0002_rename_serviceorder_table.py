from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        DO $$
                        BEGIN
                            IF to_regclass('public.orders_workorder') IS NULL
                               AND to_regclass('public.orders_serviceorder') IS NOT NULL THEN
                                ALTER TABLE public.orders_serviceorder RENAME TO orders_workorder;
                                -- renomeia a sequence se existir com o padrão antigo
                                IF to_regclass('public.orders_serviceorder_id_seq') IS NOT NULL THEN
                                    ALTER SEQUENCE public.orders_serviceorder_id_seq
                                    RENAME TO orders_workorder_id_seq;
                                END IF;
                            END IF;
                        END$$;
                    """,
                    reverse_sql="""
                        DO $$
                        BEGIN
                            IF to_regclass('public.orders_serviceorder') IS NULL
                               AND to_regclass('public.orders_workorder') IS NOT NULL THEN
                                ALTER TABLE public.orders_workorder RENAME TO orders_serviceorder;
                                IF to_regclass('public.orders_workorder_id_seq') IS NOT NULL THEN
                                    ALTER SEQUENCE public.orders_workorder_id_seq
                                    RENAME TO orders_serviceorder_id_seq;
                                END IF;
                            END IF;
                        END$$;
                    """,
                ),
            ],
            state_operations=[
                # Estado já está em WorkOrder → nenhuma mudança de state aqui.
            ],
        ),
    ]
