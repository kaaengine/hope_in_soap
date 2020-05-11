import random

from kaa.engine import Scene
from kaa.colors import Color
from kaa.geometry import Vector, Segment
from kaa.input import Keycode
from kaa.nodes import Node
from kaa.transitions import NodeTransition
from kaa.physics import (
    SpaceNode, BodyNode, HitboxNode, BodyNodeType, CollisionPhase,
)

from .constants import (
    CollisionTrigger,
    SPRITE_HAND, SPRITE_WATER_BACK, SPRITE_WATER_FRONT,
)
from .nodes import VerticalScrollingNode
from .states import PlayerState
from .managers import (
    PlayerManager, PowerupsManager, RunnersManager, EffectsManager, UIManager
)


class GameplayScene(Scene):
    def __init__(self):
        self.camera.position = Vector(0, 0)
        self.game_over = False

        # physics setup
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
                # color=Color(1., 0., 0., 0.5),
                z_index=100,
            )
        )
        self.space.set_collision_handler(
            CollisionTrigger.soap, CollisionTrigger.runner_enemy,
            self.on_collision_soap_enemy, phases_mask=CollisionPhase.begin,
        )
        self.space.set_collision_handler(
            CollisionTrigger.border, CollisionTrigger.runner_enemy,
            self.on_collision_border_enemy, phases_mask=CollisionPhase.begin,
        )
        self.space.set_collision_handler(
            CollisionTrigger.soap, CollisionTrigger.runner_pickup,
            self.on_collision_soap_pickup, phases_mask=CollisionPhase.begin,
        )
        self.space.set_collision_handler(
            CollisionTrigger.border, CollisionTrigger.runner_pickup,
            self.on_collision_border_pickup, phases_mask=CollisionPhase.begin,
        )

        # background parallax effect
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

        self.player_state = PlayerState()
        self.effects_manager = EffectsManager(
            root_node=self.root,
            camera=self.camera,
        )
        self.runners_manager = RunnersManager(
            space_node=self.space,
        )
        self.powerups_manager = PowerupsManager(
            player_state=self.player_state,
            runners_manager=self.runners_manager,
        )
        self.player_manager = PlayerManager(
            player_state=self.player_state,
            space_node=self.space,
            effects_manager=self.effects_manager,
        )
        self.ui_manager = UIManager(
            player_state=self.player_state,
            root_node=self.root,
        )

    def on_collision_soap_enemy(self, arbiter, soap_pair, enemy_pair):
        if not self.game_over:
            self.player_manager.handle_enemy_kill(enemy_pair.body)
            enemy_pair.body.handle_destruction()

    def on_collision_border_enemy(self, arbiter, border_pair, enemy_pair):
        if not self.game_over:
            self.player_manager.handle_enemy_missed(enemy_pair.body)
            enemy_pair.body.handle_destruction()

    def on_collision_soap_pickup(self, arbiter, soap_pair, pickup_pair):
        if not self.game_over:
            self.player_manager.handle_pickup_grab(pickup_pair.body)
            pickup_pair.body.handle_destruction()

    def on_collision_border_pickup(self, arbiter, border_pair, pickup_pair):
        if not self.game_over:
            pickup_pair.body.handle_destruction()

    def update(self, dt):
        for event in self.input.events():
            if event.keyboard_key:
                pressed_key = event.keyboard_key.key
                if not self.game_over:
                    if event.keyboard_key.is_key_down:
                        if pressed_key == Keycode.a or pressed_key == Keycode.left:
                            self.player_manager.move_left(True)
                        elif pressed_key == Keycode.d or pressed_key == Keycode.right:
                            self.player_manager.move_right(True)
                        elif pressed_key == Keycode.num_1:
                            self.powerups_manager.use_liquid_soap()
                        elif pressed_key == Keycode.num_2:
                            self.powerups_manager.use_antivirus()
                    else:
                        if pressed_key == Keycode.a or pressed_key == Keycode.left:
                            self.player_manager.move_left(False)
                        elif pressed_key == Keycode.d or pressed_key == Keycode.right:
                            self.player_manager.move_right(False)

        if not self.game_over:
            self.effects_manager.update_camera()
            self.player_manager.consume_fuel(dt)
            self.ui_manager.update_ui()
            if (
                self.player_state.people_counter == 0
                or self.player_state.soap_meter_counter == 0
            ):
                self.game_over = True
                self.player_manager.kill()
                self.ui_manager.show_game_over()
        # TODO gameover check
