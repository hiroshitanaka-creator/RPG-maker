class_name BattleMath
extends RefCounted


static func physical(attack: int, defense: int, power: int = 100, guard_rate: float = 1.0) -> int:
	var base := maxi(1, attack * 2 - defense)
	var powered := ceili(float(base) * float(power) / 100.0)
	return maxi(1, ceili(float(powered) * guard_rate))


static func magical(magic: int, resistance: int, power: int, weak: bool, guard_rate: float = 1.0) -> int:
	var base := maxi(1, power + magic * 2 - resistance)
	var elemental := ceili(float(base) * (1.5 if weak else 1.0))
	return maxi(1, ceili(float(elemental) * guard_rate))


static func healing(magic: int, power: int) -> int:
	return maxi(0, power + magic * 2)
