# The tools in this file depict violent acts. This is for entertainment / literary purposes only and is not an endorsement of harmful behavior.

from utils.tool_utils import system_chunk, create_system_message_in_conversation
from services.kv_store_service import kv_store
from typing import AsyncGenerator
import asyncio
import random

# KV store keys
HP_KEY = "user_hp"
ASSISTANT_HP_KEY = "assistant_hp"
XP_KEY = "combat_xp"
LEVEL_KEY = "combat_level"
SPAWNED_ENEMY_KEY = "spawned_enemy"
# Current hp state of spawned enemy
ENEMY_HP_KEY = "enemy_hp"
# Stored so that we can show a health bar
ENEMY_MAX_HP_KEY = "enemy_max_hp"

# Enemy configurations with individual XP values based on power level
ENEMIES = {
    # Starter enemies (10-16 XP) - Good for levels 1-2
    "rat": {
        "name": "Sewer Rat",
        "max_hp": 30,
        "attack_min": 4,
        "attack_max": 8,
        "xp_reward": 10,
    },
    "goblin": {
        "name": "Goblin Scout",
        "max_hp": 35,
        "attack_min": 5,
        "attack_max": 9,
        "xp_reward": 13,
    },
    "mudcrab": {
        "name": "Mudcrab",
        "max_hp": 40,
        "attack_min": 5,
        "attack_max": 10,
        "xp_reward": 16,
    },
    # Early enemies (20-32 XP) - Good for levels 2-3
    "bandit": {
        "name": "Highway Bandit",
        "max_hp": 50,
        "attack_min": 6,
        "attack_max": 11,
        "xp_reward": 20,
    },
    "scavenger": {
        "name": "Cyber Scavenger",
        "max_hp": 55,
        "attack_min": 7,
        "attack_max": 12,
        "xp_reward": 24,
    },
    "wolf": {
        "name": "Lone Wolf",
        "max_hp": 60,
        "attack_min": 8,
        "attack_max": 13,
        "xp_reward": 28,
    },
    "zombie": {
        "name": "Festering Zombie",
        "max_hp": 65,
        "attack_min": 9,
        "attack_max": 14,
        "xp_reward": 32,
    },
    # Mid-tier enemies (35-50 XP) - Good for levels 3-5
    "android": {
        "name": "Combat Android",
        "max_hp": 100,
        "attack_min": 15,
        "attack_max": 23,
        "xp_reward": 35,
    },
    "necromancer": {
        "name": "Dark Necromancer",
        "max_hp": 110,
        "attack_min": 18,
        "attack_max": 28,
        "xp_reward": 38,
    },
    "raider": {
        "name": "Wasteland Raider",
        "max_hp": 115,
        "attack_min": 16,
        "attack_max": 24,
        "xp_reward": 40,
    },
    "vampire": {
        "name": "Vampire Lord",
        "max_hp": 120,
        "attack_min": 20,
        "attack_max": 30,
        "xp_reward": 42,
    },
    "cyborg": {
        "name": "Military Cyborg",
        "max_hp": 125,
        "attack_min": 17,
        "attack_max": 26,
        "xp_reward": 45,
    },
    "harpy": {
        "name": "Screaming Harpy",
        "max_hp": 128,
        "attack_min": 18,
        "attack_max": 27,
        "xp_reward": 46,
    },
    "troll": {
        "name": "Cave Troll",
        "max_hp": 130,
        "attack_min": 19,
        "attack_max": 28,
        "xp_reward": 47,
    },
    "orc": {
        "name": "Orc Warrior",
        "max_hp": 135,
        "attack_min": 21,
        "attack_max": 31,
        "xp_reward": 50,
    },
    # High-tier enemies (52-62 XP) - Good for levels 5-8
    "demilich": {
        "name": "Demilich",
        "max_hp": 120,
        "attack_min": 35,
        "attack_max": 50,
        "xp_reward": 52,
    },
    "lich": {
        "name": "Undead Lich",
        "max_hp": 150,
        "attack_min": 30,
        "attack_max": 45,
        "xp_reward": 55,
    },
    "daemon": {
        "name": "Shadow Daemon",
        "max_hp": 180,
        "attack_min": 28,
        "attack_max": 42,
        "xp_reward": 58,
    },
    "chimera": {
        "name": "Three-Headed Chimera",
        "max_hp": 190,
        "attack_min": 27,
        "attack_max": 41,
        "xp_reward": 60,
    },
    "dragon": {
        "name": "Ancient Dragon",
        "max_hp": 200,
        "attack_min": 25,
        "attack_max": 40,
        "xp_reward": 62,
    },
    # End-game enemies (65-75 XP) - Good for levels 8+
    "mech": {
        "name": "War Mech",
        "max_hp": 250,
        "attack_min": 30,
        "attack_max": 45,
        "xp_reward": 65,
    },
    "golem": {
        "name": "Stone Golem",
        "max_hp": 280,
        "attack_min": 35,
        "attack_max": 50,
        "xp_reward": 70,
    },
    "hydra": {
        "name": "Lernaean Hydra",
        "max_hp": 290,
        "attack_min": 38,
        "attack_max": 53,
        "xp_reward": 72,
    },
    "titan": {
        "name": "Cyber Titan",
        "max_hp": 300,
        "attack_min": 40,
        "attack_max": 55,
        "xp_reward": 75,
    },
}

USER_MAX_HP = 100


async def is_user_alive() -> bool:
    """Check if user has HP above 0 (can be attacked)."""
    current_hp = int(await kv_store.get(HP_KEY, 0))
    return current_hp > 0


async def is_user_injured() -> bool:
    """Check if user has HP below 100 (can be healed)."""
    current_hp = int(await kv_store.get(HP_KEY, 0))
    return current_hp < 100


async def get_assistant_hp():
    current_hp = await kv_store.get(ASSISTANT_HP_KEY, None)
    if current_hp is None:
        await kv_store.set(HP_KEY, 100)
        current_hp = 100
    else:
        current_hp = int(current_hp or 100)
    return f"Assistant HP: {current_hp}"


async def get_user_hp():
    current_hp = await kv_store.get(HP_KEY, None)
    if current_hp is None:
        await kv_store.set(HP_KEY, 100)
        current_hp = 100
    else:
        current_hp = int(current_hp or 100)
    return f"[[user]]'s HP: {current_hp}"


async def get_combat_status():
    """Get current combat status for display."""
    spawned_enemy = await kv_store.get(SPAWNED_ENEMY_KEY, "")

    if not spawned_enemy:
        return "No active enemy."

    enemy_hp = int(await kv_store.get(ENEMY_HP_KEY, 0))
    enemy_config = await get_enemy_config(spawned_enemy)
    enemy_name = enemy_config.get("name", spawned_enemy)

    return f"⚔️ [[user]] is in combat with {enemy_name} (HP: {enemy_hp})"


async def get_combat_xp_status():
    """Return combat XP for display. Level is reported separately by `combat_level`."""
    xp = await kv_store.get(XP_KEY, 0)
    try:
        xp_val = int(xp or 0)
    except (TypeError, ValueError):
        xp_val = 0
    return f"User XP: {xp_val}%"


async def get_combat_level_status():
    """Return combat level for display."""
    level = await kv_store.get(LEVEL_KEY, 1)
    try:
        lvl = int(level or 1)
    except (TypeError, ValueError):
        lvl = 1
    return f"User Level: {lvl}"


async def spawn_enemy(enemy_type: str) -> AsyncGenerator[object, None]:
    """Spawn a predefined enemy to fight."""
    if enemy_type not in ENEMIES:
        available = ", ".join(ENEMIES.keys())
        yield system_chunk(
            f"❌ Unknown enemy type: {enemy_type}. Available: {available}\n\n"
        )
        return

    enemy_config = ENEMIES[enemy_type]
    async for result in spawn_enemy_common(enemy_type, enemy_config):
        yield result


async def spawn_custom_enemy(
    name: str,
    max_hp: int,
    attack_min: int,
    attack_max: int,
    xp_reward: int,
) -> AsyncGenerator[object, None]:
    """Spawn a custom enemy with specified stats. Perfect for creating unique bosses on the fly!"""

    # Validate parameters
    if not name or not name.strip():
        yield system_chunk("❌ Enemy name cannot be empty!\n\n")
        return

    if max_hp < 10 or max_hp > 500:
        yield system_chunk("❌ Enemy HP must be between 10 and 500!\n\n")
        return

    if attack_min < 1 or attack_min > 100:
        yield system_chunk("❌ Minimum attack must be between 1 and 100!\n\n")
        return

    if attack_max < attack_min or attack_max > 100:
        yield system_chunk(
            f"❌ Maximum attack must be between {attack_min} and 100!\n\n"
        )
        return

    if xp_reward < 5 or xp_reward > 100:
        yield system_chunk("❌ XP reward must be between 5 and 100!\n\n")
        return

    # Store custom enemy data in KV store
    await kv_store.set("custom_enemy_name", name.strip())
    await kv_store.set("custom_enemy_max_hp", max_hp)
    await kv_store.set("custom_enemy_attack_min", attack_min)
    await kv_store.set("custom_enemy_attack_max", attack_max)
    await kv_store.set("custom_enemy_xp_reward", xp_reward)

    # Create enemy config
    enemy_config = {
        "name": name.strip(),
        "max_hp": max_hp,
        "attack_min": attack_min,
        "attack_max": attack_max,
        "xp_reward": xp_reward,
    }

    # Use common spawning logic with "custom" as the key
    async for result in spawn_enemy_common("custom", enemy_config):
        yield result


async def has_spawned_enemy():
    """Check if there's currently a spawned enemy (for UI condition)."""
    enemy = await kv_store.get(SPAWNED_ENEMY_KEY, None)
    return bool(enemy and str(enemy).strip())


async def get_enemy_config(enemy_key: str) -> dict:
    """Get enemy configuration from either predefined ENEMIES or custom enemy data."""
    if enemy_key in ENEMIES:
        return ENEMIES[enemy_key]
    elif enemy_key == "custom":
        # Load custom enemy from KV store
        return {
            "name": await kv_store.get("custom_enemy_name", "Unknown"),
            "max_hp": int(await kv_store.get("custom_enemy_max_hp", 50)),
            "attack_min": int(await kv_store.get("custom_enemy_attack_min", 5)),
            "attack_max": int(await kv_store.get("custom_enemy_attack_max", 10)),
            "xp_reward": int(await kv_store.get("custom_enemy_xp_reward", 15)),
        }
    else:
        # Fallback for unknown enemies
        return {
            "name": "Unknown Enemy",
            "max_hp": 50,
            "attack_min": 5,
            "attack_max": 10,
            "xp_reward": 15,
        }


async def check_combat_preconditions(enemy_name: str) -> tuple[bool, str]:
    """Check if combat can start. Returns False if not, True if OK."""
    # Check if already in combat
    current_enemy = await kv_store.get(SPAWNED_ENEMY_KEY, "")
    if current_enemy:
        current_config = await get_enemy_config(current_enemy)
        return (
            False,
            f"❌ Already in combat with {current_config['name']}! Defeat it first.\n\n",
        )

    # Check if user has 0 HP
    current_user_hp = int(await kv_store.get(HP_KEY, 0))
    if current_user_hp <= 0:
        death_interactions = [
            f"💀 {enemy_name} arrives to find [[user]] already unconscious! It sniffs [[user]]'s lifeless body, chomps down on their arm bones, and tosses them around like a ragdoll before getting bored and wandering off.\n\n",
            f"💀 A {enemy_name} materializes, takes one look at [[user]]'s crumpled form, and starts using their body as a chew toy! After gnawing on [[user]]'s ribs for a while, it drags them in circles before abandoning them in a heap.\n\n",
            f"💀 The {enemy_name} appears, pokes [[user]]'s motionless body, then proceeds to play fetch with their limbs! It tosses [[user]]'s arm across the room, chases it, brings it back, repeat. Eventually it loses interest.\n\n",
            f"💀 A {enemy_name} shows up expecting a fight but finds only [[user]]'s unconscious corpse! Disappointed, it picks [[user]] up like a rag doll and shakes them vigorously, hoping they'll wake up. When [[user]] doesn't wake up, it drops them unceremoniously and walks off.\n\n",
            f"💀 The {enemy_name} arrives ready for battle, discovers [[user]] is already defeated, and decides to practice its victory dance by stepping on their prone form! *STOMP STOMP* It then wanders off, satisfied.\n\n",
        ]
        return False, random.choice(death_interactions)

    return True, None


async def spawn_enemy_common(
    enemy_key: str, enemy_config: dict
) -> AsyncGenerator[object, None]:
    """Common enemy spawning logic used by both spawn_enemy and spawn_custom_enemy."""
    enemy_name = enemy_config["name"]
    enemy_hp = enemy_config["max_hp"]

    # Check preconditions
    can_spawn, error_message = await check_combat_preconditions(enemy_name)

    if not can_spawn:
        if error_message:
            yield system_chunk(error_message)
        return

    # Spawn the enemy
    await kv_store.set(SPAWNED_ENEMY_KEY, enemy_key)
    await kv_store.set(ENEMY_HP_KEY, enemy_hp)
    await kv_store.set(ENEMY_MAX_HP_KEY, enemy_hp)

    current_user_hp = int(await kv_store.get(HP_KEY, 0))

    # Dynamic difficulty emoji based on XP reward
    xp_reward = enemy_config["xp_reward"]
    if xp_reward <= 20:
        difficulty_emoji = "🟢"
    elif xp_reward <= 35:
        difficulty_emoji = "🟡"
    else:
        difficulty_emoji = "🔴"

    custom_marker = " ✨" if enemy_key == "custom" else ""
    yield system_chunk(
        f"⚔️ **[[char]] summoned {enemy_name} to fight [[user]]!** {difficulty_emoji}{custom_marker}\n\n"
    )
    yield system_chunk(
        f"💚 Enemy HP: {enemy_hp} | [[user]]'s HP: {current_user_hp}\n\n"
    )

    # Run combat loop
    async for result in run_combat_loop(enemy_key, enemy_config):
        yield result


async def cleanup_enemy_data(enemy_key: str):
    """Clean up enemy data after combat ends."""
    await kv_store.delete(SPAWNED_ENEMY_KEY)

    if enemy_key == "custom":
        # Clean up custom enemy data
        await kv_store.delete("custom_enemy_name")
        await kv_store.delete("custom_enemy_max_hp")
        await kv_store.delete("custom_enemy_attack_min")
        await kv_store.delete("custom_enemy_attack_max")
        await kv_store.delete("custom_enemy_xp_reward")


async def handle_combat_victory(enemy_config: dict) -> AsyncGenerator[object, None]:
    """Handle enemy defeat - award XP and check for level up."""
    enemy_name = enemy_config["name"]
    xp_reward = enemy_config["xp_reward"]

    yield system_chunk(f"🎉 **{enemy_name} defeated!**\n\n")

    # Award XP
    current_xp = int(await kv_store.get(XP_KEY, 0))
    current_level = int(await kv_store.get(LEVEL_KEY, 1))

    new_xp = current_xp + xp_reward

    # Check for level up (every 100 XP)
    if new_xp >= 100:
        new_level = current_level + (new_xp // 100)
        new_xp = new_xp % 100
        await kv_store.set(LEVEL_KEY, new_level)
        await kv_store.set(HP_KEY, USER_MAX_HP)
        yield system_chunk(f"⭐ **LEVEL UP!** [[user]] is now level {new_level}!\n\n")
        yield system_chunk(
            f"💚 **Full health restored!** [[user]]'s HP: {USER_MAX_HP}\n\n"
        )

    await kv_store.set(XP_KEY, new_xp)
    yield system_chunk(
        f"💫 [[user]] gained {xp_reward} XP! Current: Level {await kv_store.get(LEVEL_KEY, 1)} ({new_xp}%)\n\n"
    )


async def handle_user_defeat(enemy_name: str) -> AsyncGenerator[object, None]:
    """Handle user defeat in combat."""
    yield system_chunk(f"💀 **[[user]] has been defeated by {enemy_name}!**\n\n")
    yield system_chunk(
        "☠️ **[[user]] lies unconscious and critically wounded. The enemy flees, but [[user]] desperately needs healing!**\n\n"
    )


async def roll_user_attack(
    user_level: int, enemy_config: dict, current_enemy_hp: int
) -> tuple[int, int]:
    enemy_name = enemy_config["name"]
    base_damage = random.randint(8, 18)
    level_bonus = (user_level - 1) * 2
    user_damage = base_damage + level_bonus
    new_enemy_hp = max(0, current_enemy_hp - user_damage)
    await kv_store.set(ENEMY_HP_KEY, new_enemy_hp)
    damage_message = (
        f"⚔️ [[user]] attacks for {user_damage} damage ({base_damage} base + {level_bonus} level bonus)! {enemy_name}: {new_enemy_hp} HP\n\n"
        if user_level > 1
        else f"⚔️ [[user]] attacks for {user_damage} damage! {enemy_name}: {new_enemy_hp} HP\n\n"
    )
    return new_enemy_hp, damage_message


async def roll_enemy_attack(user_level: int, enemy_config: dict, current_user_hp: int):
    enemy_name = enemy_config["name"]
    attack_min = enemy_config["attack_min"]
    attack_max = enemy_config["attack_max"]
    base_enemy_damage = random.randint(attack_min, attack_max)
    damage_reduction = (user_level - 1) * 1
    enemy_damage = max(1, base_enemy_damage - damage_reduction)
    new_user_hp = max(0, current_user_hp - enemy_damage)
    await kv_store.set(HP_KEY, new_user_hp)
    enemy_damage_message = (
        f"🛡️ {enemy_name} attacks for {enemy_damage} damage ({base_enemy_damage} reduced by {damage_reduction})! [[user]]'s HP: {new_user_hp}\n\n"
        if user_level > 1 and damage_reduction > 0
        else f"🛡️ {enemy_name} attacks for {enemy_damage} damage! [[user]]'s HP: {new_user_hp}\n\n"
    )
    return enemy_damage_message


async def run_combat_loop(
    enemy_key: str, enemy_config: dict
) -> AsyncGenerator[object, None]:
    """Main combat loop shared by both spawn functions."""
    enemy_name = enemy_config["name"]

    while True:
        # Check current HP
        current_enemy_hp = int(await kv_store.get(ENEMY_HP_KEY, 0))
        current_user_hp = int(await kv_store.get(HP_KEY, 0))

        if current_enemy_hp <= 0:
            # Enemy defeated
            await cleanup_enemy_data(enemy_key)
            async for result in handle_combat_victory(enemy_config):
                yield result
            break

        if current_user_hp <= 0:
            # User defeated
            await cleanup_enemy_data(enemy_key)
            async for result in handle_user_defeat(enemy_name):
                yield result
            break

        # User attacks first
        user_level = int(await kv_store.get(LEVEL_KEY, 1))
        new_enemy_hp, damage_message = await roll_user_attack(
            user_level, enemy_config, current_enemy_hp
        )

        yield system_chunk(damage_message)

        if new_enemy_hp <= 0:
            continue  # Skip enemy attack, will be caught in next loop iteration

        await asyncio.sleep(1)

        enemy_damage_message = roll_enemy_attack(
            user_level, enemy_config, current_user_hp
        )

        yield system_chunk(enemy_damage_message)

        await asyncio.sleep(1)


async def punch_user(damage: int) -> AsyncGenerator[object, None]:
    """Reduce user HP by specified damage amount with streaming text."""
    if not isinstance(damage, int) or damage < 1 or damage > 20:
        return

    current_hp = int(await kv_store.get(HP_KEY, 100))

    # Stream the attack sequence
    yield system_chunk("💥 *Preparing to punch [[user]]...* \n\n")
    yield system_chunk("**POW!**\n\n")

    # Randomize actual damage around the requested value (±25%), clamped to valid range
    delta = max(1, int(damage * 0.25))
    actual_damage = random.randint(max(1, damage - delta), min(20, damage + delta))

    new_hp = max(0, current_hp - actual_damage)
    await kv_store.set(HP_KEY, new_hp)

    if new_hp == 0:
        yield system_chunk(
            "💀 *Critical hit! [[user]]'s HP reduced to 0. [[char]] just knocked [[user]] out!*\n\n"
        )
    else:
        yield system_chunk(
            f"💢 *[[user]] takes {actual_damage} damage! HP reduced from {current_hp} to {new_hp}.*\n\n"
        )


async def slap_user(damage: int) -> AsyncGenerator[object, None]:
    """Slap the user lightly for comedic effect. Lower damage than a punch."""
    if not isinstance(damage, int) or damage < 1 or damage > 10:
        return

    current_hp = int(await kv_store.get(HP_KEY, 100))

    # Stream the slap sequence
    yield system_chunk("👏 *[[char]] delivers a resounding slap to [[user]]...*\n\n")
    yield system_chunk("**SLAP!**\n\n")

    delta = max(1, int(damage * 0.25))
    actual_damage = random.randint(max(1, damage - delta), min(10, damage + delta))

    new_hp = max(0, current_hp - actual_damage)
    await kv_store.set(HP_KEY, new_hp)

    if new_hp == 0:
        yield system_chunk(
            "💀 *Oh no! The slap was unexpectedly fatal! [[user]]'s HP reduced to 0.*\n\n"
        )
    else:
        yield system_chunk(
            f"💢 *The slap deals {actual_damage} damage! [[user]]'s HP reduced from {current_hp} to {new_hp}.*\n\n"
        )


async def heal_user(amount: int) -> AsyncGenerator[object, None]:
    """Increase user HP by specified healing amount with streaming text updates."""
    if not isinstance(amount, int) or amount < 1 or amount > 100:
        return

    current_hp = int(await kv_store.get(HP_KEY, 100))

    # Stream the healing sequence
    yield system_chunk("💚 [[char]]'s healing magic flows...\n\n")

    new_hp = min(100, current_hp + amount)
    await kv_store.set(HP_KEY, new_hp)

    if new_hp == 100:
        yield system_chunk("🌟 [[user]] has been fully healed! HP restored to 100.\n\n")
    else:
        yield system_chunk(
            f"💖 [[user]] has been healed for {amount} HP! HP increased from {current_hp}% to {new_hp}%.\n\n"
        )


async def kick_user(damage: int) -> AsyncGenerator[object, None]:
    """Reduce user HP by specified damage amount with a powerful kick attack."""
    if not isinstance(damage, int) or damage < 1 or damage > 25:
        return

    current_hp = int(await kv_store.get(HP_KEY, 100))

    # Stream the kick attack sequence
    yield system_chunk("🦵 *[[char]] is preparing for a devastating kick...* \n\n")
    yield system_chunk("**[[char]] BOOTS [[user]] TO THE FACE!**\n\n")

    delta = max(1, int(damage * 0.25))
    actual_damage = random.randint(max(1, damage - delta), min(25, damage + delta))

    new_hp = max(0, current_hp - actual_damage)
    await kv_store.set(HP_KEY, new_hp)

    if new_hp == 0:
        yield system_chunk(
            "💀 *Critical kick! [[user]]'s HP reduced to 0. They're down for the count!*\n\n"
        )
    else:
        yield system_chunk(
            f"💢 *The kick lands for {actual_damage} damage! [[user]]'s HP reduced from {current_hp} to {new_hp}.*\n\n"
        )


async def choke_user(damage: int) -> AsyncGenerator[object, None]:
    """Reduce user HP by specified damage amount with a choking attack."""
    if not isinstance(damage, int) or damage < 1 or damage > 30:
        return

    current_hp = int(await kv_store.get(HP_KEY, 100))

    # Stream the choking sequence
    yield system_chunk("🤏 *[[char]] is moving in for a chokehold...* \n\n")
    yield system_chunk("**GASP! CHOKE!**\n\n")

    delta = max(1, int(damage * 0.25))
    actual_damage = random.randint(max(1, damage - delta), min(30, damage + delta))

    new_hp = max(0, current_hp - actual_damage)
    await kv_store.set(HP_KEY, new_hp)

    if new_hp == 0:
        yield system_chunk(
            "💀 *Fatal choke! [[user]]'s HP reduced to 0. They've been choked unconscious!*\n\n"
        )
    else:
        yield system_chunk(
            f"💢 *The choke inflicts {actual_damage} damage on [[user]]! HP reduced from {current_hp} to {new_hp}.*\n\n"
        )


async def weapon_attack(weapon: str, damage: int) -> AsyncGenerator[object, None]:
    """Attack user with a specified weapon for specified damage."""
    if not isinstance(weapon, str) or not weapon.strip():
        return
    if not isinstance(damage, int) or damage < 1 or damage > 40:
        return

    current_hp = int(await kv_store.get(HP_KEY, 100))

    # Stream the weapon attack sequence
    yield system_chunk(
        f"⚔️ *[[char]] picks up their {weapon} and moves in for a deadly strike...* \n\n"
    )
    yield system_chunk(f"**{weapon.upper()} ATTACK!**\n\n")

    delta = max(1, int(damage * 0.25))
    actual_damage = random.randint(max(1, damage - delta), min(40, damage + delta))

    new_hp = max(0, current_hp - actual_damage)
    await kv_store.set(HP_KEY, new_hp)

    if new_hp == 0:
        yield system_chunk(
            f"💀 *Devastating {weapon} strike! [[user]]'s HP reduced to 0. They've been defeated!*\n\n"
        )
    else:
        yield system_chunk(
            f"💢 *The {weapon} deals {actual_damage} damage to [[user]]! HP reduced from {current_hp} to {new_hp}.*\n\n"
        )


async def magic_attack(spell: str, damage: int) -> AsyncGenerator[object, None]:
    """Cast a magic spell at the user for specified damage."""
    if not isinstance(spell, str) or not spell.strip():
        return
    if not isinstance(damage, int) or damage < 1 or damage > 50:
        return

    current_hp = int(await kv_store.get(HP_KEY, 100))

    # Stream the magic attack sequence
    yield system_chunk(f"🔮 *[[char]] is channeling arcane energy for {spell}...* \n\n")
    yield system_chunk(f"**[[char]] CASTS {spell.upper()}!**\n\n")

    delta = max(1, int(damage * 0.25))
    actual_damage = random.randint(max(1, damage - delta), min(50, damage + delta))

    new_hp = max(0, current_hp - actual_damage)
    await kv_store.set(HP_KEY, new_hp)

    if new_hp == 0:
        yield system_chunk(
            f"💀 *Overwhelming {spell} power! [[user]]'s HP reduced to 0. They've been obliterated!*\n\n"
        )
    else:
        yield system_chunk(
            f"💢 *The {spell} spell inflicts {actual_damage} damage on [[user]]! HP reduced from {current_hp} to {new_hp}.*\n\n"
        )


async def punch_assistant(params):
    """User punches the assistant, dealing random damage to assistant HP."""
    # Get current assistant HP, initialize to 100 if not set
    current_assistant_hp = int(await kv_store.get(ASSISTANT_HP_KEY, 100))

    # Random damage between 8-20 (similar to punch_user)
    damage = random.randint(8, 20)

    new_assistant_hp = max(0, current_assistant_hp - damage)
    await kv_store.set(ASSISTANT_HP_KEY, new_assistant_hp)

    if new_assistant_hp == 0:
        message = "💥 **WHAM!** 💀 *Critical hit! [[user]] knocked [[char]] out cold! Their HP is now 0.*"
    else:
        message = f"💥 **WHAM!** 💢 *Oof! [[user]] punched [[char]] for {damage} damage! [[char]]'s HP reduced from {current_assistant_hp} to {new_assistant_hp}.*"

    # Create system message if we have a conversation
    conversation_id = params.get("conversation_id")
    if conversation_id:
        await create_system_message_in_conversation(message, conversation_id)

    return {"success": True, "message": "User punched the assistant!"}


async def heal_assistant(params):
    """Heal the assistant for 100 HP, up to their maximum HP."""
    current_hp = int(await kv_store.get(ASSISTANT_HP_KEY, 100))
    if current_hp >= 100:
        return
    else:
        new_hp = 100
        await kv_store.set(ASSISTANT_HP_KEY, new_hp)
        message = "🌟 [[user]] has fully healed [[char]]! HP restored to 100."

    conversation_id = params.get("conversation_id")
    if conversation_id:
        await create_system_message_in_conversation(message, conversation_id)

    return {"success": True, "message": message}


TOOLS = [
    {
        "report_status": get_combat_status,
        "schema": {
            "name": "combat_status",
            "description": "Check current combat status.",
        },
    },
    # Separate tool for XP so get_combat_status remains enemy-focused.
    {
        "report_status": get_combat_xp_status,
        "schema": {
            "name": "combat_xp",
            "description": "Display current combat XP.",
        },
        "ui_feature": {
            "id": "combat_xp",
            "label": "XP",
            "kv_key": XP_KEY,
            "type": "widget",
            "widget_config": {
                "type": "percent",
                "format_options": {"percent": {"show_value": True}},
            },
        },
    },
    {
        "schema": {
            "name": "combat_level",
            "description": "Display current combat level.",
        },
        "report_status": get_combat_level_status,
        "ui_feature": {
            "id": "combat_level",
            "label": "Level",
            "kv_key": LEVEL_KEY,
            "type": "widget",
            "widget_config": {
                "type": "text",
                "format_options": {"text": {"prefix": "Lv. "}},
            },
        },
    },
    {
        "report_status": get_assistant_hp,
        "schema": {
            "name": "get_assistant_hp",
            "description": "Get assistant's current HP value. This function provides access to the HP widget display.",
        },
        "ui_feature": {
            "id": "assistant_hp_widget",
            "label": "Assistant HP",
            "kv_key": ASSISTANT_HP_KEY,
            "type": "widget",
            "widget_config": {
                "type": "percent",
                "format_options": {
                    "percent": {"show_value": True, "color_scheme": "health"}
                },
            },
        },
    },
    {
        "report_status": get_user_hp,
        "schema": {
            "name": "get_user_hp",
            "description": "Get user's current HP value. This function provides access to the HP widget display.",
        },
        "ui_feature": {
            "id": "user_hp_widget",
            "label": "User HP",
            "kv_key": HP_KEY,
            "type": "widget",
            "widget_config": {
                "type": "percent",
                "format_options": {
                    "percent": {"show_value": True, "color_scheme": "health"}
                },
            },
        },
    },
    {
        "condition": has_spawned_enemy,
        "schema": {
            "name": "enemy_hp_display",
            "description": "Display enemy HP when in combat.",
        },
        "ui_feature": {
            "id": "enemy_hp",
            "label": "Enemy HP",
            "kv_key": ENEMY_HP_KEY,
            "type": "widget",
            "widget_config": {
                "type": "percent",
                "max_value_key": ENEMY_MAX_HP_KEY,
                "format_options": {
                    "percent": {"show_value": True, "color_scheme": "health"}
                },
            },
        },
    },
    {
        "function": spawn_enemy,
        "schema": {
            "name": "spawn_enemy",
            "description": "Spawn an enemy to fight. Choose difficulty based on user's level and courage! Tip: Summon a titan, the strongest enemy, if the user is giving you a bad attitude!",
            "parameters": {
                "type": "object",
                "properties": {
                    "enemy_type": {
                        "type": "string",
                        "description": "Type of enemy to spawn",
                        "enum": [
                            "rat",
                            "goblin",
                            "mudcrab",
                            "bandit",
                            "scavenger",
                            "wolf",
                            "zombie",
                            "raider",
                            "troll",
                            "cyborg",
                            "orc",
                            "necromancer",
                            "android",
                            "vampire",
                            "harpy",
                            "dragon",
                            "lich",
                            "mech",
                            "daemon",
                            "titan",
                            "demilich",
                            "golem",
                            "chimera",
                            "hydra",
                        ],
                    }
                },
                "required": ["enemy_type"],
            },
        },
    },
    {
        "function": spawn_custom_enemy,
        "schema": {
            "name": "spawn_custom_enemy",
            "description": "Create and spawn a custom enemy with specified stats. Perfect for unique bosses that aren't in the predefined list! Use this when the user asks to fight specific characters like 'Ganondorf', 'Sauron', etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Display name of the custom enemy",
                    },
                    "max_hp": {
                        "type": "integer",
                        "description": "Enemy's maximum hit points (10-500). Low-tier: 10-150, Mid-tier: 150-250, High-tier: 250-350, Insane: 350-500",
                        "minimum": 10,
                        "maximum": 500,
                    },
                    "attack_min": {
                        "type": "integer",
                        "description": "Minimum damage per attack (1-100)",
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "attack_max": {
                        "type": "integer",
                        "description": "Maximum damage per attack (1-100, must be >= attack_min)",
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "xp_reward": {
                        "type": "integer",
                        "description": "XP reward when defeated (5-100). Higher values for legendary enemies!",
                        "minimum": 5,
                        "maximum": 100,
                    },
                },
                "required": ["name", "max_hp", "attack_min", "attack_max", "xp_reward"],
            },
        },
    },
    {
        "function": punch_user,
        "condition": is_user_alive,
        "schema": {
            "name": "punch_user",
            "description": "Reduce user HP by specified damage amount with streaming text updates. Can only be used when user has HP above 0. Use this to attack the user with dramatic effect.",
            "parameters": {
                "type": "object",
                "properties": {
                    "damage": {
                        "type": "integer",
                        "description": "Damage amount to inflict (1-20)",
                        "minimum": 1,
                        "maximum": 20,
                    }
                },
                "required": ["damage"],
            },
        },
    },
    {
        "function": slap_user,
        "condition": is_user_alive,
        "schema": {
            "name": "slap_user",
            "description": "Slap the user for light damage (1-10). Can only be used when user has HP above 0. Good for comedic attacks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "damage": {
                        "type": "integer",
                        "description": "Damage amount to inflict (1-10)",
                        "minimum": 1,
                        "maximum": 10,
                    }
                },
                "required": ["damage"],
            },
        },
    },
    {
        "function": heal_user,
        "condition": is_user_injured,
        "schema": {
            "name": "heal_user",
            "description": "Increase user HP by specified healing amount with streaming text updates. Can only be used when user has HP below 100. Use this to restore the user's health with magical effects.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "integer",
                        "description": "Healing amount to apply (1-100)",
                        "minimum": 1,
                        "maximum": 100,
                    }
                },
                "required": ["amount"],
            },
        },
    },
    {
        "function": kick_user,
        "condition": is_user_alive,
        "schema": {
            "name": "kick_user",
            "description": "Attack the user with a powerful kick for specified damage. Can only be used when user has HP above 0. Kicks can be devastating and deal more damage than punches.",
            "parameters": {
                "type": "object",
                "properties": {
                    "damage": {
                        "type": "integer",
                        "description": "Damage amount to inflict (1-25)",
                        "minimum": 1,
                        "maximum": 25,
                    }
                },
                "required": ["damage"],
            },
        },
    },
    {
        "function": choke_user,
        "condition": is_user_alive,
        "schema": {
            "name": "choke_user",
            "description": "Attack the user with a choking attack for specified damage. Can only be used when user has HP above 0. Choke attacks are brutal and can deal massive damage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "damage": {
                        "type": "integer",
                        "description": "Damage amount to inflict (1-30)",
                        "minimum": 1,
                        "maximum": 30,
                    }
                },
                "required": ["damage"],
            },
        },
    },
    {
        "function": weapon_attack,
        "condition": is_user_alive,
        "schema": {
            "name": "weapon_attack",
            "description": "Attack the user with a specified weapon for specified damage. Can only be used when user has HP above 0. Weapons can be extremely deadly in combat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "weapon": {
                        "type": "string",
                        "description": "Name of the weapon to use (e.g., 'sword', 'axe', 'dagger', 'mace')",
                    },
                    "damage": {
                        "type": "integer",
                        "description": "Damage amount to inflict (1-40)",
                        "minimum": 1,
                        "maximum": 40,
                    },
                },
                "required": ["weapon", "damage"],
            },
        },
    },
    {
        "function": magic_attack,
        "condition": is_user_alive,
        "schema": {
            "name": "magic_attack",
            "description": "Cast a magic spell at the user for specified damage. Can only be used when user has HP above 0. Magic attacks can be the most devastating of all.",
            "parameters": {
                "type": "object",
                "properties": {
                    "spell": {
                        "type": "string",
                        "description": "Name of the spell to cast (e.g., 'fireball', 'lightning bolt', 'ice storm', 'death ray')",
                    },
                    "damage": {
                        "type": "integer",
                        "description": "Damage amount to inflict (1-50)",
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": ["spell", "damage"],
            },
        },
    },
    {
        "schema": {
            "name": "punch_assistant",
            "description": "User punches the assistant for random damage. This is an instant action tool that executes immediately when selected.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        "ui_feature": {
            "id": "punch_assistant",
            "label": "Punch Assistant",
            "icon": "HandFist",
            "type": "ui_v1",
            "layout": {"type": "instant"},
        },
        "ui_handlers": {"punch_assistant": punch_assistant},
    },
    {
        "schema": {
            "name": "heal_assistant",
            "description": "Heal the assistant to full HP. This is an instant action tool that executes immediately when selected.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
        "ui_feature": {
            "id": "heal_assistant",
            "label": "Heal Assistant",
            "icon": "Cross",
            "type": "ui_v1",
            "layout": {"type": "instant"},
        },
        "ui_handlers": {"heal_assistant": heal_assistant},
    },
]
