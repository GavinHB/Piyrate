import tcod as libtcod
from random import randint

from components.ai import BasicMonster
from components.equipment import EquipmentSlots
from components.equippable import Equippable
from components.fighter import Fighter
from components.item import Item
from components.stairs import Stairs

from entity import Entity

from game_messages import Message

from item_functions import cast_bullet, cast_confuse, cast_fireball, cast_lightning, heal

from map_objects.rectangle import Rect
from map_objects.tile import Tile

from random_utils import from_dungeon_level, random_choice_from_dict

from render_functions import RenderOrder


class GameMap:
    def __init__(self, width, height, dungeon_level=1):
        self.width = width
        self.height = height
        self.tiles = self.initialize_tiles()

        self.dungeon_level = dungeon_level

    def initialize_tiles(self):
        tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]

        return tiles

    def make_map(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities):
        rooms = []
        num_rooms = 0

        center_of_last_room_x = None
        center_of_last_room_y = None

        for r in range(max_rooms):
            # random width and height
            w = randint(room_min_size, room_max_size)
            h = randint(room_min_size, room_max_size)
            # random position without going out of the boundaries of the map
            x = randint(0, map_width - w - 1)
            y = randint(0, map_height - h - 1)

            # "Rect" class makes rectangles easier to work with
            new_room = Rect(x, y, w, h)

            # run through the other rooms and see if they intersect with this one
            for other_room in rooms:
                if new_room.intersect(other_room):
                    break
            else:
                # this means there are no intersections, so this room is valid

                # "paint" it to the map's tiles
                self.create_room(new_room)

                # center coordinates of new room, will be useful later
                (new_x, new_y) = new_room.center()

                center_of_last_room_x = new_x
                center_of_last_room_y = new_y

                if num_rooms == 0:
                    # this is the first room, where the player starts at
                    player.x = new_x
                    player.y = new_y
                else:
                    # all rooms after the first:
                    # connect it to the previous room with a tunnel

                    # center coordinates of previous room
                    (prev_x, prev_y) = rooms[num_rooms - 1].center()

                    # flip a coin (random number that is either 0 or 1)
                    if randint(0, 1) == 1:
                        # first move horizontally, then vertically
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        # first move vertically, then horizontally
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)

                self.place_entities(new_room, entities)

                # finally, append the new room to the list
                rooms.append(new_room)
                num_rooms += 1

        stairs_component = Stairs(self.dungeon_level + 1)
        down_stairs = Entity(center_of_last_room_x, center_of_last_room_y, '>', libtcod.white, 'Stairs',
                            render_order=RenderOrder.STAIRS, stairs=stairs_component)
        entities.append(down_stairs)

    def create_room(self, room):
        # go through the tiles in the rectangle and make them passable
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def place_entities(self, room, entities):
        # [NUMBER OF ITEMS/MONSTERS PER ROOM, DUNGEON LEVEL]
        max_monsters_per_room = from_dungeon_level([[2, 1], [3, 4], [5, 6]], self.dungeon_level)
        max_items_per_room = from_dungeon_level([[10, 1], [2, 4]], self.dungeon_level)
        # Get a random number of monsters
        number_of_monsters = randint(0, max_monsters_per_room)

        # Get a random number of items
        number_of_items = randint(0, max_items_per_room)

        # [CHANCE OF SPAWNING, DUNGEON LEVEL]
        monster_chances = {
            'ragged_sailor': 60,
            'skeleton': from_dungeon_level([[30, 1], [40, 2], [50, 3]], self.dungeon_level),
            'troll': from_dungeon_level([[15, 1], [30, 2], [60, 3]], self.dungeon_level)
        }

        item_chances = {
            'healing_potion': 35,
            'rapier': from_dungeon_level([[5, 1]], self.dungeon_level),
            'buckler': from_dungeon_level([[15, 1]], self.dungeon_level),
            'fancy_hat': from_dungeon_level([[5, 1]], self.dungeon_level),
            'fancy_shirt': from_dungeon_level([[5, 1]], self.dungeon_level),
            'lightning_scroll': from_dungeon_level([[25, 1]], self.dungeon_level),
            'fireball_scroll': from_dungeon_level([[25, 1]], self.dungeon_level),
            'confusion_scroll': from_dungeon_level([[10, 1]], self.dungeon_level),
            'flintlock': from_dungeon_level([[50, 1]], self.dungeon_level)
        }

        for i in range(number_of_monsters):
            #Choose a random location in the room
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            # Check if an entity is already at that lockation
            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                monster_choice = random_choice_from_dict(monster_chances)

                if monster_choice == 'ragged_sailor':
                    fighter_component = Fighter(hp=15, defense=1, power=4, xp=35)
                    ai_component = BasicMonster()

                    monster = Entity(x, y, 's', libtcod.desaturated_green, 'Ragged Sailor', blocks=True,
                                    render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
                elif monster_choice == 'skeleton':
                    fighter_component = Fighter(hp=20, defense=3, power=4, xp=100)
                    ai_component = BasicMonster()

                    monster = Entity(x, y, 'k', libtcod.darker_green, 'Skeleton', blocks=True, fighter=fighter_component,
                                    render_order=RenderOrder.ACTOR, ai=ai_component)
                else:
                    fighter_component = Fighter(hp=30, defense=4, power=8, xp=100)
                    ai_component = BasicMonster()

                    monster = Entity(x, y, 'T', libtcod.darker_green, 'Troll', blocks=True, fighter=fighter_component,
                                    render_order=RenderOrder.ACTOR, ai=ai_component)

                entities.append(monster)

        for i in range(number_of_items):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                item_choice = random_choice_from_dict(item_chances)
                ## ADD SOME ITEMS HERE FOR FUN
                if item_choice == 'healing_potion':
                    item_component = Item(use_function=heal, amount=40)
                    item = Entity(x, y, '!', libtcod.violet, 'Healing Potion', render_order=RenderOrder.ITEM,
                                item=item_component)
                elif item_choice == 'rapier':
                    equippable_component = Equippable(EquipmentSlots.MAIN_HAND, power_bonus=3)
                    item = Entity(x, y, '/', libtcod.sky, 'Rapier', equippable=equippable_component)
                elif item_choice == 'buckler':
                    equippable_component = Equippable(EquipmentSlots.OFF_HAND, defense_bonus=1)
                    item = Entity(x, y, '[', libtcod.darker_orange, 'Buckler', equippable=equippable_component)
                elif item_choice == 'fancy_hat':
                    equippable_component = Equippable(EquipmentSlots.HEAD, defense_bonus=1)
                    item = Entity(x, y, '^', libtcod.crimson, 'Fancy Hat', equippable=equippable_component)
                elif item_choice == 'fancy_shirt':
                    equippable_component = Equippable(EquipmentSlots.TORSO, defense_bonus=1)
                    item = Entity(x, y, ';', libtcod.crimson, 'Fancy Shirt', equippable=equippable_component)
                elif item_choice == 'fireball_scroll':
                    item_component = Item(use_function=cast_fireball, targeting=True, targeting_message=Message(
                    'Left-click a target for the fireball, or right-click to cancel.', libtcod.light_cyan),
                                    damage=25, radius=3)
                    item = Entity(x, y, '#', libtcod.red, 'Fireball Scroll', render_order=RenderOrder.ITEM,
                                    item=item_component)
                elif item_choice == 'confusion_scroll':
                    item_component = Item(use_function=cast_confuse, targeting=True, targeting_message=Message(
                        'Left-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan))
                    item = Entity(x, y, '#', libtcod.light_pink, 'Confusion Scroll', render_order=RenderOrder.ITEM,
                                    item=item_component)
                elif item_choice == 'flintlock':
                    item_component = Item(use_function=cast_bullet, targeting=True, targeting_message=Message(
                        'Left-click an enemy to shoot it, or right-click to cancel.', libtcod.light_cyan),
                                    damage=40, maximum_range=5)
                    item = Entity(x, y, '+', libtcod.light_pink, 'Flintlock', render_order=RenderOrder.ITEM,
                                    item=item_component)
                else:
                    item_component = Item(use_function=cast_lightning, targeting=True, targeting_message=Message(
                        'Left-click an enemy to lightning strike it, or right-click to cancel.', libtcod.light_cyan),
                                    damage=40, maximum_range=5)
                    item = Entity(x, y, '#', libtcod.yellow, 'Lightning Scroll', render_order=RenderOrder.ITEM,
                                    item=item_component)

                entities. append(item)


    def is_blocked(self, x, y):
        if self.tiles[x][y].blocked:
            return True

        return False


    def next_floor(self, player, message_log, constants):
        self.dungeon_level += 1
        entities = [player]

        self.tiles = self.initialize_tiles()
        self.make_map(constants['max_rooms'], constants['room_min_size'], constants['room_max_size'],
                        constants['map_width'], constants['map_height'], player, entities)

        player.fighter.heal(player.fighter.max_hp // 2)

        message_log.add_message(Message('You take a moment to rest and recover your strength.', libtcod.light_violet))

        return entities
