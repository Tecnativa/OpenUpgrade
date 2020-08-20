# Copyright 2018 Opener B.V. (stefan@opener.amsterdam)
# Copyright 2018 Paul Catinean <https://github.com/PCatinean>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.openupgrade_records.lib import apriori
from openupgradelib import openupgrade

model_renames_product = [
    ('product.uom', 'uom.uom'),
    ('product.uom.categ', 'uom.category'),
]

model_renames_stock = [
    ('stock.incoterms', 'account.incoterms'),
]

table_renames_product = [
    ('product_uom', 'uom_uom'),
    ('product_uom_categ', 'uom_category'),
]

table_renames_stock = [
    ('stock_incoterms', 'account_incoterms'),
]

xmlid_renames = [
    ('auth_signup.default_template_user', 'base.template_portal_user_id'),
    ('auth_signup.default_template_user_config',
     'base.default_template_user_config'),
    ('product.group_uom', 'uom.group_uom'),
    ('product.product_uom_gram', 'uom.product_uom_gram'),
    ('product.product_uom_qt', 'uom.product_uom_qt'),
    ('product.product_uom_categ_unit', 'uom.product_uom_categ_unit'),
    ('product.product_uom_categ_kgm', 'uom.product_uom_categ_kgm'),
    ('product.product_uom_categ_vol', 'uom.product_uom_categ_vol'),
    ('product.uom_categ_wtime', 'uom.uom_categ_wtime'),
    ('product.uom_categ_length', 'uom.uom_categ_length'),
    ('product.product_uom_unit', 'uom.product_uom_unit'),
    ('product.product_uom_dozen', 'uom.product_uom_dozen'),
    ('product.product_uom_kgm', 'uom.product_uom_kgm'),
    ('product.product_uom_hour', 'uom.product_uom_hour'),
    ('product.product_uom_day', 'uom.product_uom_day'),
    ('product.product_uom_ton', 'uom.product_uom_ton'),
    ('product.product_uom_meter', 'uom.product_uom_meter'),
    ('product.product_uom_km', 'uom.product_uom_km'),
    ('product.product_uom_litre', 'uom.product_uom_litre'),
    ('product.product_uom_lb', 'uom.product_uom_lb'),
    ('product.product_uom_oz', 'uom.product_uom_oz'),
    ('product.product_uom_cm', 'uom.product_uom_cm'),
    ('product.product_uom_inch', 'uom.product_uom_inch'),
    ('product.product_uom_foot', 'uom.product_uom_foot'),
    ('product.product_uom_mile', 'uom.product_uom_mile'),
    ('product.product_uom_floz', 'uom.product_uom_floz'),
    ('product.product_uom_gal', 'uom.product_uom_gal'),
    ('stock.incoterm_CFR', 'account.incoterm_CFR'),
    ('stock.incoterm_CIF', 'account.incoterm_CIF'),
    ('stock.incoterm_CIP', 'account.incoterm_CIP'),
    ('stock.incoterm_CPT', 'account.incoterm_CPT'),
    ('stock.incoterm_DAF', 'account.incoterm_DAF'),
    ('stock.incoterm_DAP', 'account.incoterm_DAP'),
    ('stock.incoterm_DAT', 'account.incoterm_DAT'),
    ('stock.incoterm_DDP', 'account.incoterm_DDP'),
    ('stock.incoterm_DDU', 'account.incoterm_DDU'),
    ('stock.incoterm_DEQ', 'account.incoterm_DEQ'),
    ('stock.incoterm_DES', 'account.incoterm_DES'),
    ('stock.incoterm_EXW', 'account.incoterm_EXW'),
    ('stock.incoterm_FAS', 'account.incoterm_FAS'),
    ('stock.incoterm_FCA', 'account.incoterm_FCA'),
    ('stock.incoterm_FOB', 'account.incoterm_FOB'),
]

_obsolete_tables = (
    "stock_location_path",
)


def switch_noupdate_flag(env):
    """"Some renamed XML-IDs have changed their noupdate status, so we change
    it as well.
    """
    openupgrade.logged_query(
        env.cr, """
        UPDATE ir_model_data
        SET noupdate=False
        WHERE module='base' AND name
            IN ('default_template_user_config', 'template_portal_user_id')""",
    )


def eliminate_duplicate_translations(cr):
    # Deduplicate code translations
    openupgrade.logged_query(
        cr, """
        DELETE FROM ir_translation WHERE id IN (
            SELECT id FROM (
                SELECT id, row_number() over (
                    partition BY type, src, lang ORDER BY id
                ) AS rnum FROM ir_translation WHERE type = 'code'
            ) t WHERE t.rnum > 1
        )""")
    # Deduplicate model translations on the same record
    openupgrade.logged_query(
        cr, """
        DELETE FROM ir_translation WHERE id IN (
            SELECT id FROM (
                SELECT id, row_number() over (
                    partition BY type, name, res_id, lang ORDER BY id
                ) AS rnum FROM ir_translation WHERE type = 'model'
            ) t WHERE t.rnum > 1
        )""")
    # Deduplicate various
    openupgrade.logged_query(
        cr, """
        DELETE FROM ir_translation WHERE id IN (
            SELECT id FROM (
                SELECT id, row_number() over (
                    partition BY type, name, src, lang ORDER BY id
                ) AS rnum FROM ir_translation WHERE
                    type IN ('selection', 'constraint', 'sql_constraint',
                             'view', 'field', 'help', 'xsl', 'report')
            ) t WHERE t.rnum > 1
        )""")


def fix_lang_constraints(env):
    """Avoid error on normal update process due to the removal + re-addition of
    constraints.
    """
    openupgrade.logged_query(
        env.cr, """ALTER TABLE ir_translation
        DROP CONSTRAINT ir_translation_lang_fkey_res_lang
        """,
    )


def fix_lang_table(env):
    """Avoid error on normal update process due to changed language codes"""
    openupgrade.logged_query(
        env.cr, "UPDATE res_lang SET code='km_KH' WHERE code='km_KM'"
    )


def fill_ir_ui_view_key(cr):
    openupgrade.logged_query(
        cr,
        """
        UPDATE ir_ui_view
        SET key = COALESCE(split_part(
            arch_fs, '/', 1), 'website') || '.' || replace(
                lower(trim(both from name)), ' ', '_') || '_view'
        WHERE type = 'qweb' AND key IS NULL
        """
    )


def fill_ir_attachment_res_model_name(cr):
    # fast compute the res_model_name in ir.attachment
    if not openupgrade.column_exists(cr, 'ir_attachment', 'res_model_name'):
        openupgrade.logged_query(
            cr, """
            ALTER TABLE ir_attachment ADD COLUMN res_model_name varchar""",
        )
        openupgrade.logged_query(
            cr, """
            UPDATE ir_attachment ia
            SET res_model_name = im.name
            FROM ir_model im
            WHERE im.model = ia.res_model""",
        )


def _migrate_rma(env):
    cr = env.cr
    # Migration scripts to be able to use in v12 'rma' and 'rma_sale'
    # modules from OCA/rma instead of the existing private modules
    # rma_ept and website_rma_ept.
    openupgrade.update_module_names(
        cr, [("rma_ept", "rma"), ("website_rma_ept", "rma_sale")], merge_modules=True,
    )
    openupgrade.rename_models(cr, [("rma.reason.ept", "rma.operation")])
    openupgrade.rename_tables(cr, [("rma_reason_ept", "rma_operation")])
    # set 'claim.line.ept' as the main rma table renaming it to 'rma'
    openupgrade.rename_models(cr, [("claim.line.ept", "rma")])
    openupgrade.rename_tables(cr, [("claim_line_ept", "rma")])
    # Remove incorrect lines
    openupgrade.logged_query(cr, "DELETE FROM rma WHERE claim_id IS NULL")
    # Rename security groups
    openupgrade.rename_xmlids(
        env.cr, [
            ("rma_ept.group_rma_user_ept", "rma.rma_group_user_all"),
            ("rma_ept.group_rma_manager_ept", "rma.rma_group_manager"),
        ]
    )
    # Rename existing fields in the new rma table to be compatible
    # with rma v12 module
    openupgrade.rename_fields(
        env,
        [
            ("rma", "rma", "quantity", "product_uom_qty"),
            ("rma", "rma", "rma_reason_id", "operation_id"),
        ],
    )
    # Add non-existing field in the new rma table to be filled
    openupgrade.add_fields(
        env,
        [
            ("sent", "rma", "rma", "boolean", False, "rma"),
            ("name", "rma", "rma", "char", False, "rma"),
            ("origin", "rma", "rma", "char", False, "rma"),
            ("date", "rma", "rma", "datetime", False, "rma"),
            ("deadline", "rma", "rma", "date", False, "rma"),
            ("user_id", "rma", "rma", "many2one", False, "rma"),
            ("company_id", "rma", "rma", "many2one", False, "rma"),
            ("partner_id", "rma", "rma", "many2one", False, "rma"),
            ("partner_invoice_id", "rma", "rma", "many2one", False, "rma"),
            ("picking_id", "rma", "rma", "many2one", False, "rma"),
            ("product_uom", "rma", "rma", "many2one", False, "rma"),
            ("priority", "rma", "rma", "selection", False, "rma"),
            ("state", "rma", "rma", "selection", False, "rma"),
            ("description", "rma", "rma", "text", False, "rma"),
            ("location_id", "rma", "rma", "many2one", False, "rma"),
            ("reception_move_id", "rma", "rma", "many2one", False, "rma"),
            ("refund_id", "rma", "rma", "many2one", False, "rma"),
            ("refund_line_id", "rma", "rma", "many2one", False, "rma"),
            # rma_sale module
            ("order_id", "rma", "rma", "many2one", False, "rma_sale"),
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE rma AS r
        SET description = cce.name || E'\n' || cce.description || E'\n'
                || cce.cause || E'\n' || cce.resolution,
            sent = cce.rma_send,
            name = cce.code,
            date = cce.date,
            deadline = cce.date_deadline,
            user_id = cce.user_id,
            company_id = cce.company_id,
            partner_id = cce.partner_id,
            picking_id = cce.picking_id,
            priority = cce.priority,
            location_id = cce.location_id,
            order_id = so.id,
            origin = so.name,
            partner_invoice_id = so.partner_invoice_id,
            product_uom = sm.product_uom,
            state = (
                CASE
                    WHEN cce.state = 'approve' THEN 'confirmed'
                    WHEN cce.state = 'process' THEN 'received'
                    WHEN cce.state = 'reject' THEN 'cancelled'
                    WHEN (cce.state = 'close' AND r.claim_type = 'refund')
                        THEN 'refunded'
                    WHEN (cce.state = 'close' AND r.claim_type = 'replace')
                        THEN 'replaced'
                    WHEN (cce.state = 'close' AND r.claim_type = 'repair')
                        THEN 'returned'
                END
            )
        FROM
            crm_claim_ept AS cce,
            stock_picking AS sp,
            sale_order AS so,
            stock_move AS sm
        WHERE
            r.claim_id = cce.id
            AND cce.picking_id = sp.id
            AND sp.sale_id = so.id
            AND r.move_id = sm.id
        """,
    )
    # Find matching refund and refund line
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE rma AS r
        SET
            refund_line_id = ail.id,
            refund_id = ai_cce.account_invoice_id
        FROM
            crm_claim_ept AS cce,
            account_invoice_crm_claim_ept_rel AS ai_cce,
            account_invoice_line AS ail
        WHERE
            r.claim_id = cce.id
            AND ai_cce.crm_claim_ept_id = cce.id
            AND ai_cce.account_invoice_id = ail.invoice_id
            AND r.product_id = ail.product_id
        """,
    )
    # Find matching reception_move_id
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE rma AS r
        SET reception_move_id = sm.id
        FROM
            stock_move AS sm,
            crm_claim_ept AS cce
        WHERE
            r.claim_id = cce.id
            AND cce.return_picking_id = sm.picking_id
            AND r.product_id = sm.product_id
        """,
    )
    # Set rma_id in account.invoice.line
    openupgrade.add_fields(
        env,
        [
            (
                "rma_id",
                "account.invoice.line",
                "account_invoice_line",
                "many2one",
                False,
                "rma",
            )
        ],
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_invoice_line AS ail
        SET rma_id = r.id
        FROM rma AS r
        WHERE r.refund_line_id = ail.id
        """,
    )
    # Set rma_id in stock.picking
    openupgrade.add_fields(
        env, [("rma_id", "stock.move", "stock_move", "many2one", False, "rma")],
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE stock_move AS sm
        SET rma_id = r.id
        FROM
            crm_claim_ept_stock_picking_rel AS cce_sp,
            rma AS r
        WHERE
            sm.picking_id = cce_sp.stock_picking_id
            AND r.claim_id = cce_sp.crm_claim_ept_id
            AND r.product_id = sm.product_id
        """,
    )


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    openupgrade.remove_tables_fks(env.cr, _obsolete_tables)
    # Deactivate the noupdate flag (hardcoded on initial SQL load) for allowing
    # to update changed data on this group.
    openupgrade.logged_query(
        env.cr, """
        UPDATE ir_model_data SET noupdate=False
        WHERE  module='base' AND name='group_user'""",
    )
    openupgrade.update_module_names(
        env.cr, apriori.renamed_modules.items())
    openupgrade.update_module_names(
        env.cr, apriori.merged_modules.items(), merge_modules=True)
    if openupgrade.table_exists(env.cr, 'product_uom'):
        openupgrade.rename_models(env.cr, model_renames_product)
        openupgrade.rename_tables(env.cr, table_renames_product)
    if openupgrade.table_exists(env.cr, 'stock_incoterms'):
        openupgrade.rename_models(env.cr, model_renames_stock)
        openupgrade.rename_tables(env.cr, table_renames_stock)
    openupgrade.rename_xmlids(env.cr, xmlid_renames)
    switch_noupdate_flag(env)
    eliminate_duplicate_translations(env.cr)

    # Make the system and admin user XML ids refer to the same entry for now to
    # prevent errors when base data is loaded. The users are picked apart in
    # this module's end stage migration script.
    # Safely, we check first if the `base.user_admin` already exists to
    # avoid possible conflicts: very old databases may have this record.
    env.cr.execute("""
        SELECT id
        FROM ir_model_data
        WHERE name='user_admin' AND module='base' AND model='res.users'""")
    if env.cr.fetchone():
        env.cr.execute("""
            UPDATE ir_model_data
            SET model='res.users',res_id=1,noupdate=true
            WHERE name='user_admin' AND module='base' AND model='res.users'""")
    else:
        env.cr.execute("""
            INSERT INTO ir_model_data
            (module, name, model, res_id, noupdate)
            VALUES('base', 'user_admin', 'res.users', 1, true)""")
    env.cr.execute(
        """ INSERT INTO ir_model_data
        (module, name, model, res_id, noupdate)
        (SELECT module, 'partner_admin', model, res_id, noupdate
         FROM ir_model_data WHERE module = 'base' AND name = 'partner_root')
        """)
    fix_lang_constraints(env)
    fix_lang_table(env)
    # fast compute of res_model_name
    fill_ir_attachment_res_model_name(env.cr)
    # for migration of web module
    openupgrade.rename_columns(
        env.cr, {'res_company': [('external_report_layout', None)]})
    # for migration of website module
    fill_ir_ui_view_key(env.cr)
    openupgrade.set_xml_ids_noupdate_value(
        env, 'base', [
            'default_template_user_config',
            'view_menu',
            'lang_km',
        ], False)
    _migrate_rma(env)
