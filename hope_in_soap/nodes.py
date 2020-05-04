import typing
import random

from kaa.nodes import Node
from kaa.sprites import Sprite
from kaa.physics import BodyNode, HitboxNode, BodyNodeType
from kaa.geometry import Vector, Polygon, Circle
from kaa.transitions import (
    NodeTransition, NodeTransitionsSequence, NodeTransitionCallback,
    NodeSpriteTransition,
)

from .constants import (
    CollisionTrigger,
    SPRITE_FRAMES_SOAP, SPRITE_FRAMES_MINI_SOAP, SPRITE_FRAMES_VIRUS,
    LANE_ENEMY_SLOTS, LANE_HERO_SLOTS, SPRITE_OIL,
    SPRITE_LIQUID_SOAP, SPRITE_ANTIVIRUS
)


class VerticalScrollingNode(Node):
    def __init__(self, *, repeat_sprite, scroll_duration, z_index, **kwargs):
        self.vertical_move = repeat_sprite.dimensions.y
        super().__init__(
            transition=NodeTransition(
                Node.position, Vector(0., self.vertical_move),
                loops=0, duration=scroll_duration
            ),
            **kwargs,
        )

        self.repeat_1 = self.add_child(Node(
            sprite=repeat_sprite,
            z_index=z_index,
        ))
        self.repeat_2 = self.add_child(Node(
            sprite=repeat_sprite,
            position=Vector(0., -self.vertical_move),
            z_index=z_index,
        ))


class SoapNode(BodyNode):
    SPRITE_FRAMES = SPRITE_FRAMES_SOAP
    FRAME_DURATION = 60

    def __init__(self, **kwargs):
        self.is_moving = False
        self.is_frozen = False
        self.current_lane = 2
        self.soap_fuel = self.soap_fuel_max = 30000

        super().__init__(
            body_type=BodyNodeType.kinematic,
            position=LANE_HERO_SLOTS[self.current_lane],
            scale=Vector.xy(0.7),
            **kwargs,
        )

        self.hitbox = self.add_child(
            HitboxNode(
                trigger_id=CollisionTrigger.soap,
                shape=Polygon.from_box(Vector(138, 330)),
                # color=Color(1., 0., 0., 0.5),
                z_index=100,
            )
        )

        self.transitions_manager.set(
            'animation',
            NodeSpriteTransition(self.SPRITE_FRAMES, loops=0,
                                 duration=len(self.SPRITE_FRAMES)
                                 * self.FRAME_DURATION),
        )

    def _on_end_frozen(self, _):
        self.is_frozen = False


class LaneRunnerBase(BodyNode):
    SPRITE_FRAMES = None
    FRAME_DURATION = 60
    TRIGGER_ID = None

    def __init__(self, *, speed_mod, **kwargs):
        assert self.SPRITE_FRAMES
        assert self.TRIGGER_ID

        super().__init__(
            body_type=BodyNodeType.kinematic,
            position=random.choice(LANE_ENEMY_SLOTS),
            velocity=Vector(0, random.uniform(
                300, 300 + speed_mod
            )),
            angular_velocity_degrees=random.uniform(-20, 20),
            **kwargs,
        )
        self._is_destroying = False

        self.hitbox = self.add_child(
            HitboxNode(
                trigger_id=self.TRIGGER_ID,
                shape=Circle(48.),
                # color=Color(1., 0., 0., 0.5),
                z_index=100,
            )
        )

        self.transitions_manager.set(
            'animation',
            NodeSpriteTransition(
                self.SPRITE_FRAMES, loops=0,
                duration=len(self.SPRITE_FRAMES) * self.FRAME_DURATION
            ),
        )

    def handle_destruction(self):
        if self._is_destroying:
            return

        self._is_destroying = True

        self.hitbox.delete()
        self.transitions_manager.set(
            'destruction',
            NodeTransitionsSequence([
                NodeTransition(Node.scale, Vector(0.01, 0.01), duration=400.),
                NodeTransitionCallback(lambda n: n.delete()),
            ]),
        )

    def slowdown(self, fraction: float):
        self.velocity *= fraction


class VirusRunner(LaneRunnerBase):
    SPRITE_FRAMES = SPRITE_FRAMES_VIRUS
    TRIGGER_ID = CollisionTrigger.runner_enemy


class OilRunner(LaneRunnerBase):
    SPRITE_FRAMES = [SPRITE_OIL]
    TRIGGER_ID = CollisionTrigger.runner_pickup


class MiniSoapRunner(LaneRunnerBase):
    SPRITE_FRAMES = SPRITE_FRAMES_MINI_SOAP
    TRIGGER_ID = CollisionTrigger.runner_pickup


class LiquidSoapRunner(LaneRunnerBase):
    SPRITE_FRAMES = [SPRITE_LIQUID_SOAP]
    TRIGGER_ID = CollisionTrigger.runner_pickup


class AntivirusRunner(LaneRunnerBase):
    SPRITE_FRAMES = [SPRITE_ANTIVIRUS]
    TRIGGER_ID = CollisionTrigger.runner_pickup


class CounterStatusUINode(Node):
    def __init__(
        self, position: Vector,
        powerup_sprite: typing.Union[Sprite, typing.List[Sprite]],
            max_count: int, break_count: int = 0,
            minor_sep: Vector = Vector(0, -30),
            major_sep: Vector = Vector(100, 0),
    ):
        super().__init__(position=position)
        self.single_powerups = [
            self.add_child(
                Node(
                    position=self._calculate_position(i, break_count,
                                                      minor_sep, major_sep),
                    sprite=(
                        random.choice(powerup_sprite)
                        if isinstance(powerup_sprite, list)
                        else powerup_sprite
                    ),
                    z_index=50 + i,
                    visible=False,
                )
            ) for i in range(max_count)
        ]
        self.current_count = 0

    def _calculate_position(self, index: int, break_count: int,
                            minor_sep: Vector, major_sep: Vector):
        if break_count:
            minor_index = index % break_count
            major_index = index // break_count
            return minor_sep * minor_index + major_sep * major_index
        else:
            return minor_sep * index

    def update_count(self, new_count: int):
        if new_count < self.current_count:
            for powerup in self.single_powerups[new_count:self.current_count]:
                powerup.visible = False
        elif new_count > self.current_count:
            for powerup in self.single_powerups[self.current_count:new_count]:
                powerup.visible = True
        self.current_count = new_count
