import numpy as np

from . import orbitx_pb2 as protos


class PhysicsEntity(object):
    def __init__(self, entity):
        assert isinstance(entity, protos.Entity)
        self.name = entity.name
        self.pos = np.asarray([entity.x, entity.y])
        self.R = entity.r
        self.v = np.asarray([entity.vx, entity.vy])
        self.m = entity.mass
        self.spin = entity.spin
        self.heading = entity.heading
        self.fuel = entity.fuel
        self.throttle = entity.throttle
        self.attached_to = entity.attached_to
        self.broken = entity.broken
        self.artificial = entity.artificial

    def as_proto(self):
        return protos.Entity(
            name=self.name,
            x=self.pos[0],
            y=self.pos[1],
            vx=self.v[0],
            vy=self.v[1],
            r=self.R,
            mass=self.m,
            spin=self.spin,
            heading=self.heading,
            fuel=self.fuel,
            throttle=self.throttle,
            attached_to=self.attached_to,
            broken=self.broken,
            artificial=self.artificial
        )


# A note about functions with the signature "(self, *, arg1=None, arg2=None"
# there are a lot of float parameters to the upcoming APIs, so I think it's
# best for the callsite to have to specify what argument is what. For example,
# habitat.fuel_cons(throttle=0.2)
# as opposed to
# habitat.fuel_cons(0.2)
# The former is hopefully much clearer, so I think mandatory keyword arguments
# is better in this case.

class Engine(object):
    def __init__(self, *, max_fuel_cons=None, max_acc=None):
        """
        max_fuel_cons: kg/s consumption of fuel at max throttle
        max_acc: m/s/s acceleration from engine at max throttle
        """
        assert max_fuel_cons is not None
        assert max_acc is not None
        self._max_fuel_cons = max_fuel_cons
        self._max_acc = max_acc  # max acceleration

    def fuel_cons(self, *, throttle=None):
        assert throttle is not None
        return abs(throttle) * self._max_fuel_cons

    def acceleration(self, *, throttle=None):
        """
        throttle: unitless float, nominally in the range [0, 1]
        fuel: kg of fuel available for engine to burn
        returns the amount of linear acceleration generated by the engine.
        """
        assert throttle is not None
        return throttle * self._max_acc


class ReactionWheel(object):
    def __init__(self, *, max_spin_change=None):
        """
        max_spin_change: radians/s/s, maximum angular acceleration
        """
        assert max_spin_change is not None
        self._max_spin_change = max_spin_change

    def spin_change(self, *, requested_spin_change=None):
        """
        requested_spin_change: radians/s/s
        returns the requested spin change, bounded by max_spin_change
        """
        assert requested_spin_change is not None
        if requested_spin_change < -self._max_spin_change:
            return -self._max_spin_change
        elif requested_spin_change > self._max_spin_change:
            return self._max_spin_change
        else:
            return requested_spin_change


class Habitat():
    """Static class implementing hab engine and reaction wheel constraints."""
    engine = Engine(max_fuel_cons=10, max_acc=100)
    rw = ReactionWheel(max_spin_change=1)

    @classmethod
    def spin_change(cls, *, requested_spin_change=None):
        assert requested_spin_change is not None
        return cls.rw.spin_change(
            requested_spin_change=requested_spin_change)

    @classmethod
    def fuel_cons(cls, *, throttle=None):
        assert throttle is not None
        return abs(cls.engine.fuel_cons(throttle=throttle))

    @classmethod
    def acceleration(cls, *, throttle=None, heading=None):
        assert throttle is not None
        assert heading is not None
        acc = cls.engine.acceleration(throttle=throttle)
        return np.cos(heading) * acc, np.sin(heading) * acc
