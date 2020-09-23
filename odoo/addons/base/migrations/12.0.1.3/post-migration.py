# © 2018 Opener B.V. (stefan@opener.amsterdam)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade
from openupgradelib.openupgrade_merge_records import _change_generic
from psycopg2 import sql


def generate_thumbnails(env):
    """ Let Odoo create a thumbnail for all attachments that consist of one of
    the supported image types and are not linked to a binary field. """
    for chunk in openupgrade.chunked(
            env['ir.attachment'].search([
                ('res_field', '=', False),
                ('mimetype', 'like', 'image.%'),
                '|', ('mimetype', 'like', '%gif'),
                '|', ('mimetype', 'like', '%jpeg'),
                '|', ('mimetype', 'like', '%jpg'),
                ('mimetype', 'like', '%png')])):
        for attachment in chunk.with_context(prefetch_fields=False).read(
                ['datas', 'mimetype']):
            res = env['ir.attachment']._make_thumbnail(attachment)
            if res.get('thumbnail'):
                env['ir.attachment'].browse(attachment['id']).write({
                    'thumbnail': res['thumbnail']})


def update_res_company_onboarding_company_state(env):
    # based on old base_onboarding_company_done
    good_companies = env["res.company"].search([]).filtered(lambda c: (
        c.partner_id.browse(
            c.partner_id.sudo().address_get(adr_pref=['contact'])['contact']
        ).sudo().street
    ))
    good_companies.write({'base_onboarding_company_state': 'done'})

def _migrate_rma(env):
    # Migration scripts to be able to use in v12 'rma' and 'rma_sale' modules from 
    # OCA/rma instead of the existing private modules rma_ept and website_rma_ept.
    # Current RMAs come from the old `claim.line.ept` but all the main stuff was in
    # the parent model `crm.claim.ept`, so we must move it and adjust the proper ids.
    # We'll need to duplicate the followers records for the cases where the parent
    # model had several lines, wich are now independent entities with ther own mixins.
    mapping = [
        ('ir_attachment', 'res_model'),
        ('mail_message', 'model'),
        ('mail_activity', 'res_model'),
        ('mail_followers', 'res_model'),
    ]
    for table, model_column in mapping:
        openupgrade.logged_query(
            env.cr, sql.SQL("""
            UPDATE {table} SET {model_column}='rma'
            WHERE {model_column}='crm.claim.ept'
            """).format(
                table=sql.Identifier(table),
                model_column=sql.Identifier(model_column),
            ),
        )
    # Map `crm_claim_ept_id` with current `rma` corresponding to the old lines
    claim_ept_map = dict()
    env.cr.execute("SELECT id, claim_id FROM rma WHERE claim_id IS NOT NULL")
    for id, claim_id in env.cr.fetchall():
        claim_ept_map.setdefault(claim_id, [])
        claim_ept_map[claim_id].append(id)
    for claim_ept_id in claim_ept_map.keys():
        rma_ids = claim_ept_map[claim_ept_id]
        # Use the method just over the first id as they can't share messages
        # attachments, etc
        _change_generic(env, "rma", [claim_ept_id], rma_ids[0], [])
    # Copy followers if the parent `crm_claim_ept` had multiple lines
    for claim_ept_id in claim_ept_map.keys():
        rma_ids = claim_ept_map[claim_ept_id]
        env["rma"].browse(rma_ids[0]).
        for dup_id in rma_ids[1:]:
            openupgrade.logged_query(
                env.cr,
                """
                    INSERT INTO mail_followers(
                        channel_id, partner_id, res_id, res_model)
                    SELECT channel_id, partner_id, %s, res_model
                    FROM mail_followers
                    WHERE res_model = 'rma' AND res_id = %s;
                """ % (dup_id, rma_ids[0]),
            )

@openupgrade.migrate(use_env=True)
def migrate(env, version):
    env['ir.ui.menu']._parent_store_compute()
    env['res.partner.category']._parent_store_compute()
    generate_thumbnails(env)
    update_res_company_onboarding_company_state(env)
    openupgrade.load_data(
        env.cr, 'base', 'migrations/12.0.1.3/noupdate_changes.xml')
    # Activate back the noupdate flag on the group
    openupgrade.logged_query(
        env.cr, """
        UPDATE ir_model_data SET noupdate=True
        WHERE  module='base' AND name='group_user'""",
    )
    _migrate_rma(env)
