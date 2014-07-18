#!/usr/bin/env python
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from decimal import Decimal
import datetime
from dateutil.relativedelta import relativedelta
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
        self.period = POOL.get('stock.period')

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
            lost_found, = self.location.search([('type', '=', 'lost_found')])
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
                        'from_location': lost_found.id,
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

            with transaction.set_context(products=[product.id]):
                party = self.party(party.id)
                self.assertEqual(party.quantity, 5.0)

            move, = self.move.create([{
                        'product': product.id,
                        'uom': kg.id,
                        'quantity': 5,
                        'from_location': lost_found.id,
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
                        'from_location': lost_found.id,
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

    def test0020period(self):
        'Test period'
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            unit, = self.uom.search([('name', '=', 'Unit')])
            template, = self.template.create([{
                        'name': 'Test period',
                        'type': 'goods',
                        'cost_price_method': 'fixed',
                        'default_uom': unit.id,
                        'list_price': Decimal(0),
                        'cost_price': Decimal(0),
                        }])
            product, = self.product.create([{
                        'template': template.id,
                        }])
            lost_found, = self.location.search([('type', '=', 'lost_found')])
            storage, = self.location.search([('code', '=', 'STO')])
            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin'),
                    ])
            currency = company.currency
            self.user.write([self.user(USER)], {
                'main_company': company.id,
                'company': company.id,
                })

            party1, = self.party.create([{
                        'name': 'Party 1',
                        }])

            lot1, = self.lot.create([{
                        'product': product.id,
                        'number': '1',
                        }])

            today = datetime.date.today()

            moves = self.move.create([{
                        'product': product.id,
                        'party': party1.id,
                        'lot': lot1.id,
                        'uom': unit.id,
                        'quantity': 5,
                        'from_location': lost_found.id,
                        'to_location': storage.id,
                        'planned_date': today - relativedelta(days=1),
                        'effective_date': today - relativedelta(days=1),
                        'company': company.id,
                        'unit_price': Decimal('1'),
                        'currency': currency.id,
                        }, {
                        'product': product.id,
                        'lot': lot1.id,
                        'uom': unit.id,
                        'quantity': 10,
                        'from_location': lost_found.id,
                        'to_location': storage.id,
                        'planned_date': today - relativedelta(days=1),
                        'effective_date': today - relativedelta(days=1),
                        'company': company.id,
                        'unit_price': Decimal('1'),
                        'currency': currency.id,
                        }, {
                        'product': product.id,
                        'lot': None,
                        'party': None,
                        'uom': unit.id,
                        'quantity': 3,
                        'from_location': lost_found.id,
                        'to_location': storage.id,
                        'planned_date': today - relativedelta(days=1),
                        'effective_date': today - relativedelta(days=1),
                        'company': company.id,
                        'unit_price': Decimal('1'),
                        'currency': currency.id,
                        }])
            self.move.do(moves)

            period, = self.period.create([{
                        'date': today - relativedelta(days=1),
                        'company': company.id,
                        }])
            self.period.close([period])
            self.assertEqual(period.state, 'closed')

            quantities = {
                lost_found: -18,
                storage: 18,
                }
            for cache in period.caches:
                self.assertEqual(cache.product, product)
                self.assertEqual(cache.internal_quantity,
                    quantities[cache.location])

            quantities = {
                (lost_found, lot1, party1): -5,
                (storage, lot1, party1): 5,
                (lost_found, lot1, None): -10,
                (storage, lot1, None): 10,
                (lost_found, None, None): -3,
                (storage, None, None): 3,
                }
            for lot_party_cache in period.lot_party_caches:
                self.assertEqual(lot_party_cache.product, product)
                self.assertEqual(lot_party_cache.internal_quantity,
                    quantities[(lot_party_cache.location, lot_party_cache.lot,
                            lot_party_cache.party)])


def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite:
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestCase))
    return suite
