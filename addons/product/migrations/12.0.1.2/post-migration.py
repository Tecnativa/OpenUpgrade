# Copyright 2018 Eficent <http://www.eficent.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade, openupgrade_90
from psycopg2.extensions import AsIs


def map_product_attribute_create_variant(cr):
    # cannot use map_values method because it cannot map from a boolean
    openupgrade.logged_query(
        cr, """UPDATE product_attribute
        SET create_variant = 'always'
        WHERE %s
        """, (AsIs(openupgrade.get_legacy_name('create_variant')), ),
    )
    openupgrade.logged_query(
        cr, """UPDATE product_attribute
        SET create_variant = 'no_variant'
        WHERE NOT %s
        """, (AsIs(openupgrade.get_legacy_name('create_variant')), ),
    )

def _migrate_website_product_attribute_image(env):
    openupgrade.update_module_names(
        env.cr, [(
            "website_product_attribute_image",
            "website_sale_product_detail_attribute_value_image",
        )], merge_modules=True,
    )
    openupgrade.rename_columns(
        env.cr, {"product_attribute_value": [("attr_image", None)]}
    )
    openupgrade.rename_fields(
        env,
        [
            (
                "product.attribute.value",
                "product_attribute_value",
                "attr_image",
                "website_product_detail_image",
            )
        ],
    )
    openupgrade_90.convert_binary_field_to_attachment(
        env,
        {"product.attribute.value": [
            ("website_product_detail_image", 
             openupgrade.get_legacy_name("attr_image")),
        ]},
    )


@openupgrade.migrate()
def migrate(env, version):
    env['product.category']._parent_store_compute()
    map_product_attribute_create_variant(env.cr)
    _migrate_website_product_attribute_image(env)
