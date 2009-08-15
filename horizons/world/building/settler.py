# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

from random import randint
import logging

import horizons.main

from horizons.gui.tabs import TabWidget, OverviewTab
from horizons.util import WeakList
from building import BasicBuilding, Selectable
from buildable import BuildableSingle
from horizons.constants import RES, UNITS, SETTLER
from horizons.world.storage import PositiveSizedSpecializedStorage
from horizons.world.building.collectingproducerbuilding import CollectingProducerBuilding
from horizons.world.production.production import Production

class Settler(Selectable, BuildableSingle, CollectingProducerBuilding, BasicBuilding):
	"""Represents a settlers house, that uses resources and creates inhabitants."""
	log = logging.getLogger("world.building.settler")
	def __init__(self, x, y, owner, instance = None, level=0, **kwargs):

		super(Settler, self).__init__(x=x, y=y, owner=owner, instance=instance, level=level, **kwargs)
		self.__init(SETTLER.HAPPINESS_INIT_VALUE, level)
		self.run()

	def __init(self, happiness, level):
		self.level = level
		self.inventory.alter(RES.HAPPINESS_ID, happiness)
		self._tax_income = horizons.main.db("SELECT tax_income FROM settler_level WHERE level=?", self.level)[0][0]
		self._update_consumation()

	def _update_consumation(self):
		"""Resets the production line in case of level change, etc."""
		import pdb ; pdb.set_trace()
		# Settler productions are specified to be disabled by default in the db.
		# we enable them here by level
		current_lines = self.get_production_lines()
		for (prod_line,) in horizons.main.db("SELECT production_line FROM settler_production_line WHERE \
																			level = ?", self.level):
			if not self.has_production_line(prod_line):
				self.add_production_by_id(prod_line)

			# cross out the new lines from the current lines, so only the old ones remain
			if prod_line in current_lines:
				current_lines.remove(prod_line)

		for line in current_lines:
			# all lines, that were added here but are not needed due to the current level
			self.remove_production_by_id(line)

	def run(self):
		"""Start regular tick calls"""
		interval_in_ticks = horizons.main.session.timer.get_ticks(SETTLER.TICK_INTERVAL)
		horizons.main.session.scheduler.add_new_object(self.tick, self, runin=interval_in_ticks, \
																									 loops=-1)

	def tick(self):
		"""Here we collect the functions, that are called regularly."""
		import pdb ; pdb.set_trace()
		self.pay_tax()
		self.inhabitant_check()
		self.level_check()

	def pay_tax(self):
		"""Pays the tax for this settler"""
		# the money comes from nowhere, settlers seem to have an infinite amount of money.
		# TODO: set the amount of tax in relation to the number of settlers
		taxes = self._tax_income
		self.settlement.owner.inventory.alter(RES.GOLD_ID, taxes)
		# decrease our happiness for the amount of the taxes
		self.inventory.alter(RES.HAPPINESS_ID, taxes)
		self.log.debug("%s: pays %s taxes, new happiness: %s", self, taxes, \
									 self.inventory[RES.HAPPINESS_ID])

	def inhabitant_check(self):
		"""Checks wether or not the population of this settler should increase or decrease"""
		happiness = self.inventory[RES.HAPPINESS_ID]
		if happiness > SETTLER.HAPPINESS_INHABITANTS_INCREASE_REQUIREMENT and \
			 self.inhabitants < self.inhabitants_max:
			self.inhabitants += 1
			self.log.debug("%s: inhabitants increase to %s", self, self.inhabitants)
		elif happiness < SETTLER.HAPPINESS_INHABITANTS_DECREASE_LIMIT and self.inhabitants > 1:
			self.inhabitants -= 1
			self.log.debug("%s: inhabitants decrease to %s", self, self.inhabitants)

	def level_check(self):
		"""Checks wether we should level up or down."""
		happiness = self.inventory[RES.HAPPINESS_ID]
		# TODO: add consumtion of construction material
		if happiness > SETTLER.HAPPINESS_LEVEL_UP_REQUIREMENT:
			pass
			#self.level_up()
		elif happiness < SETTLER.HAPPINESS_LEVEL_DOWN_LIMIT:
			pass
			#self.level_down()

	def level_up(self):
		#TODO: implement leveling of settlers
		if (self.level+1) <= self.level_max:
			self.level += 1
			self.update_world_level()

	def level_down(self):
		#TODO: implement leveling of settlers
		if (self.level-1) > 0:
			self.level -= 1
			self.update_world_level()

	def update_world_level(self):
		horizons.main.session.world.player.settler_level = max(horizons.main.session.world.player.settler_level, self.level)

	def show_menu(self):
		horizons.main.session.ingame_gui.show_menu(TabWidget(tabs = [OverviewTab(self)]))

	def save(self, db):
		super(Settler, self).save(db)
		db("INSERT INTO settler(rowid, level, inhabitants) VALUES (?, ?, ?)", self.getId(), self.level, self.inhabitants)
		"""
		for (res, row) in self.consumation.iteritems():
			db("INSERT INTO settler_consume(settler_id, res, contentment, next_consume, consume_state) VALUES (?, ?, ?, ?, ?)", self.getId(), res, row['consume_contentment'], row['next_consume'], row['consume_state'])
			"""

	def load(self, db, building_id):
		super(Settler, self).load(db, building_id)
		self.level, self.inhabitants = \
				db("SELECT level, inhabitants FROM settler WHERE rowid=?", building_id)[0]
		self.__init()
		"""
		for (res, contentment, next_consume, consume_state) in db("SELECT res, contentment, next_consume, consume_state FROM settler_consume WHERE settler_id=?", self.getId()):
			self.consumation[res]['consume_contentment'] = contentment
			self.consumation[res]['next_consume'] = next_consume
			self.consumation[res]['consume_state'] = consume_state
		"""
		self.run()
