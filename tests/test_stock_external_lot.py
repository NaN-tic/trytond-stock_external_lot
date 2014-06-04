#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal
import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT, test_view,\
    test_depends
from trytond.transaction import Transaction
from trytond.exceptions import UserError


class TestCase(unittest.TestCase):
    'Test module'

    def setUp(self):
        trytond.tests.test_tryton.install_module('stock_external_lot')
        self.template = POOL.get('product.template')
        self.product = POOL.get('product.product')
        self.party = POOL.get('party.party')
        self.category = POOL.get('product.category')
        self.uom = POOL.get('product.uom')
        self.location = POOL.get('stock.location')
        self.move = POOL.get('stock.move')
        self.lot = POOL.get('stock.lot')
        self.shipment = POOL.get('stock.shipment.external')
        self.company = POOL.get('company.company')
        self.user = POOL.get('res.user')

    def test0005views(self):
        'Test views'
        test_view('stock_external_lot')

    def test0006depends(self):
        'Test depends'
        test_depends()

    def test0010stock_external_lot(self):
        'Test stock external lot'
        with Transaction().start(DB_NAME, USER,
                context=CONTEXT) as transaction:
            category, = self.category.create([{
                        'name': 'Test products_by_location',
                        }])
            kg, = self.uom.search([('name', '=', 'Kilogram')])
            g, = self.uom.search([('name', '=', 'Gram')])
            template, = self.template.create([{
                        'name': 'Test Stock Lot external',
                        'type': 'goods',
                        'list_price': Decimal(0),
                        'cost_price': Decimal(0),
                        'category': category.id,
                        'cost_price_method': 'fixed',
                        'default_uom': kg.id,
                        }])
            product, = self.product.create([{
                        'template': template.id,
                        }])
            supplier, = self.location.search([('code', '=', 'SUP')])
            customer, = self.location.search([('code', '=', 'CUS')])
            storage, = self.location.search([('code', '=', 'STO')])
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin'),
                    ])
            currency = company.currency
            self.user.write([self.user(USER)], {
                'main_company': company.id,
                'company': company.id,
                })

            party, party2 = self.party.create([{
                        'name': 'Customer',
                        }, {
                        'name': 'Customer 2',
                        }])
            self.assertEqual(party.customer_location, customer)
            self.assertEqual(party.supplier_location, supplier)

            lot1, lot2 = self.lot.create([{
                        'product': product.id,
                        'number': '1',
                        }, {
                        'product': product.id,
                        'number': '2',
                        }])

            #Recieve products from customer
            move, = self.move.create([{
                        'product': product.id,
                        'uom': kg.id,
                        'quantity': 5,
                        'from_location': customer.id,
                        'to_location': storage.id,
                        'company': company.id,
                        'unit_price': Decimal('1'),
                        'currency': currency.id,
                        'lot': lot1.id,
                        'party_used': party.id,
                        }])
            lot1 = self.lot(lot1.id)
            self.assertEqual(lot1.party, party)
            self.move.do([move])

            with self.assertRaises(UserError):
                self.move.create([{
                            'product': product.id,
                            'uom': kg.id,
                            'quantity': 5,
                            'from_location': customer.id,
                            'to_location': storage.id,
                            'company': company.id,
                            'unit_price': Decimal('1'),
                            'currency': currency.id,
                            'lot': lot1.id,
                            'party_used': party2.id,
                            }])

            with transaction.set_context(products=[product.id]):
                party = self.party(party.id)
                self.assertEqual(party.quantity, -5.0)

            move, = self.move.create([{
                        'product': product.id,
                        'uom': kg.id,
                        'quantity': 5,
                        'from_location': customer.id,
                        'to_location': storage.id,
                        'company': company.id,
                        'unit_price': Decimal('1'),
                        'currency': currency.id,
                        'lot': lot1.id,
                        }])
            self.assertEqual(move.party, party)
            move, = self.move.create([{
                        'product': product.id,
                        'uom': kg.id,
                        'quantity': 5,
                        'from_location': customer.id,
                        'to_location': storage.id,
                        'company': company.id,
                        'unit_price': Decimal('1'),
                        'currency': currency.id,
                        'lot': lot2.id,
                        }])
            self.assertIsNone(move.party)
            self.assertIsNone(move.party_used)
            move.party_used = party2
            move.save()
            self.assertEqual(move.party_used, party2)
            self.assertEqual(move.party, party2)


def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite:
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite
