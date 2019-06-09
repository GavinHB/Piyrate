import tcod as libtcod

from components.ai import ConfusedMonster

from game_messages import Message


def heal(*args, **kwargs):
    entity = args[0]
    amount = kwargs.get('amount')

    results = []

    if entity.fighter.hp == entity.fighter.max_hp:
        results.append({'consumed': False, 'message': Message('You are already at full health', libtcod.yellow)})
    else:
        entity.fighter.heal(amount)
        results.append({'consumed': True, 'message': Message('You feel reinvigorated!', libtcod.green)})

    return results
 ## GIVE THE LIGHTNING SCROLL THE ABILITY TO TARGET!
def cast_lightning(*args, **kwargs):
    caster = args[0]
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    damage = kwargs.get('damage')
    maximum_range = kwargs.get('maximum_range')
    target_x = kwargs.get('target_x')
    target_y = kwargs.get('target_y')

    results = []

    target = None
    closest_distance = maximum_range + 1

    for entity in entities:
        if entity.x == target_x and entity.y == target_y:

            target = entity


    if target:
        results.append({'consumed': True, 'target': target, 'message': Message('A lightning bolt strikes the {0} with a lour thunder! It deals {1} damage.'.format(target.name, damage))})
        results.extend(target.fighter.take_damage(damage))
    else:
        results.append({'consumed': False, 'message': Message('There is no targetable enemy at that location.', libtcod.yellow)})


    return results

def cast_bullet(*args, **kwargs):
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    damage = kwargs.get('damage')
    maximum_range = kwargs.get('maximum_range')
    target_x = kwargs.get('target_x')
    target_y = kwargs.get('target_y')

    results = []

    target = None
    closest_distance = maximum_range + 1

    for entity in entities:
        if entity.x == target_x and entity.y == target_y:

            target = entity

    if target:
        results.append({'consumed': True, 'target': target, 'message': Message('The flintlock pistol fires {0}! It deals {1} damage.'.format(target.name, damage))})
        results.extend(target.fighter.take_damage(damage))
    else:
        results.append({'consumed': False, 'message': Message('There is no targetable enemy at that location.', libtcod.yellow)})


    return results

def cast_fireball(*args, **kwargs):
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    damage = kwargs.get('damage')
    radius = kwargs.get('radius')
    target_x = kwargs.get('target_x')
    target_y = kwargs.get('target_y')

    results = []

    if not libtcod.map_is_in_fov(fov_map, target_x, target_y):
        results.append({'consumed': False, 'message': Message('You cannot target a tile outside your field of view.', libtcod.yellow)})
        return results

    results.append({'consumed': True, 'message': Message('The fireball explodes, burning everything within {0} tiles!'.format(radius), libtcod.orange)})

    for entity in entities:
        if entity.distance(target_x, target_y) <= radius and entity.fighter:
            results.append({'message': Message('The {0} gets burned for {1} damage.'.format(entity.name, damage), libtcod.orange)})
            results.extend(entity.fighter.take_damage(damage))

    return results


def cast_confuse(*args, **kwargs):
    entities = kwargs.get('entities')
    fov_map = kwargs.get('fov_map')
    target_x = kwargs.get('target_x')
    target_y = kwargs.get('target_y')

    results = []

    if not libtcod.map_is_in_fov(fov_map, target_x, target_y):
        results.append({'consumed': False, 'message': Message('You cannot target a tile outside your field of view.')})
        return results

    for entity in entities:
        if entity.x == target_x and entity.y == target_y and entity.ai:
            confused_ai = ConfusedMonster(entity.ai, 10)

            confused_ai.owner = entity
            entity.ai = confused_ai

            results.append({'consumed': True, 'message': Message('The eyes of the {0} look vacant as he starts to stumble around.'.format(entity.name), libtcod.light_green)})

            break

    else:
        results.append({'consumed': False, 'message': Message('There is no targetable enemy at that location.', libtcod.yellow)})

    return results
