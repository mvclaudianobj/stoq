# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from kiwi.datatypes import currency

from stoqlib.domain.sellable import (BaseSellableInfo,
                                     Sellable,
                                     SellableCategory)
from stoqlib.domain.product import Product
from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.domain.views import (ProductFullStockView,
                                  ProductFullWithClosedStockView,
                                  ProductClosedStockView)


class TestSellableCategory(DomainTest):
    def setUp(self):
        DomainTest.setUp(self)
        base_category = SellableCategory(description="Monitor",
                                         connection=self.trans)
        self._category = SellableCategory(description="LCD",
                                          category=base_category,
                                          connection=self.trans)

    def testGetDescription(self):
        self.failUnless(self._category.get_description() == "LCD")
        self.failUnless(self._category.get_full_description() == "Monitor LCD")

    def testMarkup(self):
        self._category.suggested_markup = currency(10)
        self._category.category.suggested_markup = currency(20)
        self.failUnless(self._category.get_markup() == currency(10))
        self._category.suggested_markup = None
        self.failUnless(self._category.get_markup() == currency(20))

    def testGetBaseCategories(self):
        categories = SellableCategory.get_base_categories(self.trans)
        count = categories.count()
        base_category = SellableCategory(description="Monitor",
                                         connection=self.trans)
        category = SellableCategory(description="LCD Monitor",
                                    category=base_category,
                                    connection=self.trans)
        categories = SellableCategory.get_base_categories(self.trans)
        self.failUnless(base_category in categories)
        self.failIf(category in categories)
        self.assertEqual(categories.count(), count + 1)

    def testGetTaxConstant(self):
        base_category = SellableCategory(description="Monitor",
                                         connection=self.trans)
        category = SellableCategory(description="LCD Monitor",
                                    category=base_category,
                                    connection=self.trans)

        self.assertEquals(category.get_tax_constant(), None)

        constant = self.create_sellable_tax_constant()
        base_category.tax_constant = constant
        self.assertEquals(category.get_tax_constant(), constant)

        constant2 = self.create_sellable_tax_constant()
        category.tax_constant = constant2
        self.assertEquals(category.get_tax_constant(), constant2)

class TestSellable(DomainTest):
    def setUp(self):
        DomainTest.setUp(self)
        self._base_category = SellableCategory(description="Cigarro",
                                               connection=self.trans)
        self._category = SellableCategory(description="Hollywood",
                                          category=self._base_category,
                                          suggested_markup=10,
                                          connection=self.trans)

    def test_price_based_on_category_markup(self):
        # When the price isn't defined, but the category and the cost. In this
        # case the sellable must have the price calculated applying the category's
        # markup in the sellable's cost.
        self._category.suggested_markup = 0
        sellable_info = BaseSellableInfo(description=u"MX123",
                                         max_discount=0,
                                         commission=0,
                                         connection=self.trans)
        sellable = Sellable(base_sellable_info=sellable_info,
                            cost=100,
                            category=self._category,
                            connection=self.trans)
        product = Product(sellable=sellable, connection=self.trans)
        self.failUnless(sellable.markup == self._category.get_markup(),
                        ("Expected markup: %r, got %r"
                         % (self._category.get_markup(),
                            sellable.markup)))
        price = sellable.cost * (sellable.markup / currency(100) + 1)
        self.failUnless(sellable.price == price,
                        ("Expected price: %r, got %r"
                         % (price, sellable.price)))

    def test_price_based_on_specified_markup(self):
        # When the price isn't defined, but the category, markup and the cost.
        # In this case the category's markup must be ignored and the price
        # calculated applying the markup specified in the sellable's cost.
        sellable_info = BaseSellableInfo(description=u"FY123",
                                         connection=self.trans)
        markup = 5
        sellable = Sellable(base_sellable_info=sellable_info,
                            category=self._category,
                            markup=markup,
                            cost=100,
                            connection=self.trans)
        product = Product(sellable=sellable, connection=self.trans)
        self.failUnless(sellable.markup == markup,
                        ("Expected markup: %r, got %r"
                         % (markup, sellable.markup)))
        price = sellable.cost * (markup / currency(100) + 1)
        self.failUnless(sellable.price == price,
                        ("Expected price: %r, got %r"
                         % (price, sellable.price)))

    def test_commission(self):
        sellable_info = BaseSellableInfo(description=u"TX342",
                                         connection=self.trans)
        self._category.salesperson_commission = 10
        sellable = Sellable(base_sellable_info=sellable_info,
                            category=self._category,
                            connection=self.trans)
        product = Product(sellable=sellable, connection=self.trans)
        self.failUnless(sellable.commission
                        == self._category.salesperson_commission,
                        ("Expected salesperson commission: %r, got %r"
                         % (self._category.salesperson_commission,
                            sellable.commission)))

    def test_prices_and_markups(self):
        sellable_info = BaseSellableInfo(description="Test", price=currency(100),
                                         connection=self.trans)
        self._category.markup = 0
        sellable = Sellable(category=self._category, cost=50,
                            base_sellable_info=sellable_info,
                            connection=self.trans)
        product = Product(sellable=sellable, connection=self.trans)
        self.failUnless(sellable.price == 100,
                        "Expected price: %r, got %r" % (100, sellable.price))
        self.failUnless(sellable.markup == 100,
                        "Expected markup: %r, got %r" % (100, sellable.markup))
        sellable.markup = 10
        self.failUnless(sellable.price == 55,
                        "Expected price: %r, got %r" % (55, sellable.price))
        sellable.price = 50
        self.failUnless(sellable.markup == 0,
                        "Expected markup %r, got %r" % (0, sellable.markup))

        # When the price specified isn't equivalent to the markup specified.
        # In this case the price don't must be updated based on the markup.
        sellable_info = BaseSellableInfo(description="Test", price=currency(100),
                                         connection=self.trans)
        sellable = Sellable(markup=10, cost=50,
                            base_sellable_info=sellable_info,
                            connection=self.trans)
        product = Product(sellable=sellable, connection=self.trans)
        self.failUnless(sellable.price == 100)

        # A simple test: product without cost and price, markup must be 0
        sellable.cost = currency(0)
        sellable.price = currency(0)
        self.failUnless(sellable.markup == 0,
                        "Expected markup %r, got %r" % (0, sellable.markup))

    def testIsValidPrice(self):
        sellable_info = BaseSellableInfo(description="Test",
                                         price=currency(100),
                                         max_discount=0,
                                         connection=self.trans)
        sellable = Sellable(category=self._category, cost=50,
                            base_sellable_info=sellable_info,
                            connection=self.trans)
        self.assertFalse(sellable.is_valid_price(0))
        self.assertFalse(sellable.is_valid_price(-10))
        self.assertFalse(sellable.is_valid_price(99))
        self.assertTrue(sellable.is_valid_price(101))
        self.assertTrue(sellable.is_valid_price(100))

        sellable.base_sellable_info.max_discount = 10
        self.assertFalse(sellable.is_valid_price(0))
        self.assertFalse(sellable.is_valid_price(-1))
        self.assertFalse(sellable.is_valid_price(89))
        self.assertTrue(sellable.is_valid_price(90))
        self.assertTrue(sellable.is_valid_price(95))
        self.assertTrue(sellable.is_valid_price(99))
        self.assertTrue(sellable.is_valid_price(101))

    def testGetTaxConstant(self):
        base_category = SellableCategory(description="Monitor",
                                         connection=self.trans)
        category = SellableCategory(description="LCD Monitor",
                                    category=base_category,
                                    connection=self.trans)
        sellable = self.create_sellable()
        sellable.tax_constant = None
        sellable.category = category

        self.assertEquals(sellable.get_tax_constant(), None)

        constant = self.create_sellable_tax_constant()
        base_category.tax_constant = constant
        self.assertEquals(sellable.get_tax_constant(), constant)

        constant2 = self.create_sellable_tax_constant()
        category.tax_constant = constant2
        self.assertEquals(sellable.get_tax_constant(), constant2)

        constant3 = self.create_sellable_tax_constant()
        sellable.tax_constant = constant3
        self.assertEquals(sellable.get_tax_constant(), constant3)

    def testClose(self):
        results_not_closed = ProductFullStockView.select(connection=self.trans)
        results_with_closed = ProductFullWithClosedStockView.select(
                                                         connection=self.trans)
        results_only_closed = ProductClosedStockView.select(
                                                         connection=self.trans)
        # Count the already there results. ProductClosedStockView should
        # not have any.
        count_not_closed = results_not_closed.count()
        count_with_closed = results_with_closed.count()
        count_only_closed = results_only_closed.count()
        self.assertEqual(count_only_closed, 0)

        # Here we create a sellable. It should show on
        # ProductFullStockView and ProductFullWithClosedStock View,
        # but not on ProductClosedStockView.
        sellable = self.create_sellable()
        self.assertEqual(results_not_closed.count(), count_not_closed + 1L)
        self.assertEqual(results_with_closed.count(), count_with_closed + 1L)
        self.assertEqual(results_only_closed.count(), count_only_closed)
        ids = [result.id for result in results_not_closed]
        self.failIf(sellable.id not in ids)
        ids = [result.id for result in results_with_closed]
        self.failIf(sellable.id not in ids)
        ids = [result.id for result in results_only_closed]
        self.failIf(sellable.id in ids)

        # Here we close that sellable. It should now show on
        # ProductClosedStockViewand ProductFullWithClosedStock View,
        # but not on ProductFullStockView.
        sellable.close()
        self.assertEquals(sellable.status, Sellable.STATUS_CLOSED)
        self.assertTrue(sellable.is_closed())
        self.assertEqual(results_not_closed.count(), count_not_closed)
        self.assertEqual(results_with_closed.count(), count_with_closed + 1L)
        self.assertEqual(results_only_closed.count(), count_only_closed + 1L)
        ids = [result.id for result in results_not_closed]
        self.failIf(sellable.id in ids)
        ids = [result.id for result in results_with_closed]
        self.failIf(sellable.id not in ids)
        ids = [result.id for result in results_only_closed]
        self.failIf(sellable.id not in ids)

        # When trying to close an already closed sellable, it should
        # raise a ValueError.
        self.assertRaises(ValueError, sellable.close)
