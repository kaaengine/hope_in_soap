import random
import enum

from kaa.engine import Engine, Scene
from kaa.sprites import Sprite, split_spritesheet
from kaa.colors import Color
from kaa.nodes import Node
from kaa.physics import (
    SpaceNode, BodyNode, BodyNodeType, HitboxNode, CollisionPhase,
)
from kaa.geometry import Vector, Circle, Polygon, Segment
from kaa.transitions import (
    NodePositionTransition, NodeTransitionsSequence, NodeSpriteTransition,
    NodeScaleTransition, NodeTransitionCallback, NodeTransitionDelay,
    NodeColorTransition, AttributeTransitionMethod,
)
from kaa.input import Keycode
from kaa.timers import Timer


SPRITE_WATER_BACK = Sprite('assets/bg.png')
SPRITE_WATER_FRONT = Sprite('assets/fasterbg.png')
SPRITE_HAND = Sprite('assets/hand.png')
SPRITE_FRAMES_SOAP = split_spritesheet(
    Sprite('assets/soapthis.png'), Vector(138, 364),
)
SPRITE_FRAMES_VIRUS = split_spritesheet(
    Sprite('assets/coronavirus.png'), Vector(90, 109),
)

LANE_HERO_SLOTS = [
    Vector(3 + (109 * i), 220)
    for i in range(-2, 3)
]

LANE_ENEMY_SLOTS = [
    Vector(3 + (109 * i), -500)
    for i in range(-2, 3)
]


class CollisionTrigger(enum.IntEnum):
    border = enum.auto()
    soap = enum.auto()
    enemy = enum.auto()


class VerticalScrollingNode(Node):
    def __init__(self, *, repeat_sprite, scroll_duration, z_index, **kwargs):
        self.vertical_move = repeat_sprite.dimensions.y
        super().__init__(
            transition=NodePositionTransition(
                Vector(0., self.vertical_move),
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
        self.current_lane = 2

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

    def move_lane(self, movement_dir: int):
        if (
                not self.is_moving
                and 0 <= self.current_lane + movement_dir < len(LANE_HERO_SLOTS)
        ):
            self.is_moving = True
            self.current_lane += movement_dir
            self.transitions_manager.set(
                'movement',
                NodeTransitionsSequence([
                    NodePositionTransition(LANE_HERO_SLOTS[self.current_lane],
                                           duration=150.),
                    NodeTransitionCallback(self._on_end_movement),
                ]),
            )

    def _on_end_movement(self, _):
        self.is_moving = False


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


class VirusRunner(LaneRunnerBase):
    SPRITE_FRAMES = SPRITE_FRAMES_VIRUS
    TRIGGER_ID = CollisionTrigger.enemy

    def handle_destruction(self):
        self.hitbox.delete()
        self.transitions_manager.set('animation', None)
        self.transitions_manager.set(
            'destruction',
            NodeTransitionsSequence([
                NodeScaleTransition(Vector(0.01, 0.01), duration=400.),
                NodeTransitionCallback(lambda n: n.delete()),
            ]),
        )
        self.time_to_live = 1000


class GameplayScene(Scene):
    def __init__(self):
        self.camera.position = Vector(0, 0)
        # self.camera.scale = Vector.xy(0.25)

        self.space = self.root.add_child(
            SpaceNode(
                sprite=SPRITE_HAND,
            )
        )
        self.space_static = self.space.add_child(
            BodyNode(
                body_type=BodyNodeType.static,
            )
        )
        self.border = self.space_static.add_child(
            HitboxNode(
                position=Vector(0, 350),
                shape=Segment(Vector(-600, 0),
                              Vector(600, 0)),
                trigger_id=CollisionTrigger.border,
                color=Color(1., 0., 0., 0.5),
                z_index=100,
            )
        )

        self.water_back = self.root.add_child(
            VerticalScrollingNode(
                repeat_sprite=SPRITE_WATER_BACK,
                scroll_duration=9000.,
                z_index=-10,
            )
        )
        self.water_front = self.root.add_child(
            VerticalScrollingNode(
                repeat_sprite=SPRITE_WATER_FRONT,
                scroll_duration=3000.,
                z_index=10,
            )
        )
        self.soap = self.space.add_child(
            SoapNode(
                z_index=15,
            )
        )

        self.flash = self.root.add_child(
            Node(
                shape=Polygon.from_box(Vector(1400, 800)),
                color=Color(0., 0., 0., 0.),
                z_index=50,
            )
        )
        self.camera_shake_ticks = 0
        self.speed_mod = 0.

        self.spawn_timer = Timer(300, self._spawn_callback, single_shot=False)
        self.spawn_timer.start()

        self.speed_timer = Timer(300, self._speed_increase_callback, single_shot=False)
        self.speed_timer.start()

        self.space.set_collision_handler(
            CollisionTrigger.soap, CollisionTrigger.enemy,
            self.on_collision_soap_enemy, phases_mask=CollisionPhase.begin,
        )
        self.space.set_collision_handler(
            CollisionTrigger.border, CollisionTrigger.enemy,
            self.on_collision_border_enemy, phases_mask=CollisionPhase.begin,
        )

    def _spawn_callback(self):
        if random.random() > max(0.80 - self.speed_mod / 1000., 0.5):
            self.space.add_child(
                VirusRunner(speed_mod=self.speed_mod, z_index=20)
            )

    def _speed_increase_callback(self):
        self.speed_mod += 2.5

    def handle_player_hit(self):
        self.camera_shake_ticks = 15
        self.color = Color(0., 0., 0., 0.)
        self.flash.transition = [
            NodeColorTransition(
                Color(1., 0., 0., 0.3), duration=200.,
            ),
            NodeColorTransition(
                Color(0., 0., 0., 0.0), duration=100.,
            )
        ]

    def on_collision_soap_enemy(self, arbiter, soap_pair, enemy_pair):
        enemy_pair.body.handle_destruction()

    def on_collision_border_enemy(self, arbiter, border_pair, enemy_pair):
        enemy_pair.body.handle_destruction()
        self.handle_player_hit()

    def update(self, dt):
        for event in self.input.events():
            if event.keyboard_key and event.keyboard_key.is_key_down:
                pressed_key = event.keyboard_key.key
                if pressed_key == Keycode.a or pressed_key == Keycode.left:
                    self.soap.move_lane(-1)
                elif pressed_key == Keycode.d or pressed_key == Keycode.right:
                    self.soap.move_lane(1)

        if self.camera_shake_ticks:
            if self.camera_shake_ticks > 1:
                self.camera.position = Vector(
                    random.uniform(-10, 10),
                    random.uniform(-10, 10),
                )
            else:
                self.camera.position = Vector(0, 0)
            self.camera_shake_ticks -= 1


def main():
    with Engine(virtual_resolution=Vector(1280, 720)) as engine:
        engine.run(GameplayScene())


if __name__ == '__main__':
    main()
