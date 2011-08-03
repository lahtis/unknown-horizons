# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from horizons.ai.aiplayer.buildingevaluator import BuildingEvaluator
from horizons.ai.aiplayer.constants import BUILDING_PURPOSE
from horizons.entities import Entities
from horizons.util.python import decorators
from horizons.constants import BUILDINGS

class ToolmakerEvaluator(BuildingEvaluator):
	def __init__(self, area_builder, builder, distance_to_smeltery, distance_to_charcoal_burner, distance_to_lumberjack, distance_to_collector, alignment):
		super(ToolmakerEvaluator, self).__init__(area_builder, builder)
		self.distance_to_smeltery = distance_to_smeltery
		self.distance_to_charcoal_burner = distance_to_charcoal_burner
		self.distance_to_lumberjack = distance_to_lumberjack
		self.distance_to_collector = distance_to_collector
		self.alignment = alignment

		personality = area_builder.owner.personality_manager.get('ToolmakerEvaluator')
		distance = self._weighted_sum(distance_to_collector, [(personality.smeltery_distance_importance, distance_to_smeltery), \
			(personality.charcoal_burner_distance_importance, distance_to_charcoal_burner), (personality.lumberjack_distance_importance, distance_to_lumberjack)])
		self.value = float(Entities.buildings[BUILDINGS.TOOLMAKER_CLASS].radius) / distance + alignment * personality.alignment_importance

	@classmethod
	def create(cls, area_builder, x, y, orientation):
		builder = area_builder.make_builder(BUILDINGS.TOOLMAKER_CLASS, x, y, True, orientation)
		if not builder:
			return None

		distance_to_collector = cls.distance_to_nearest_collector(area_builder, builder)
		if distance_to_collector is None:
			return None

		distance_to_smeltery = cls.distance_to_nearest_building(area_builder, builder, BUILDINGS.SMELTERY_CLASS)
		distance_to_charcoal_burner = cls.distance_to_nearest_building(area_builder, builder, BUILDINGS.CHARCOAL_BURNER_CLASS)
		distance_to_lumberjack = cls.distance_to_nearest_building(area_builder, builder, BUILDINGS.LUMBERJACK_CLASS)
		alignment = cls.get_alignment(area_builder, builder.position.tuple_iter())
		return ToolmakerEvaluator(area_builder, builder, distance_to_smeltery, distance_to_charcoal_burner, distance_to_lumberjack, distance_to_collector, alignment)

	@property
	def purpose(self):
		return BUILDING_PURPOSE.BRICKYARD

decorators.bind_all(ToolmakerEvaluator)
