# Copyright 2021 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE rating_rating
        SET publisher_id = rp.id,
            publisher_datetime = rr.write_date
        FROM rating_rating rr
            LEFT JOIN res_users ru ON rr.write_uid = ru.id
            LEFT JOIN res_partner rp ON ru.partner_id = rp.id
        """,
    )
