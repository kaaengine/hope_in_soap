import random

from kaa.nodes import Node
from kaa.fonts import TextNode, Font
from kaa.geometry import Polygon, Vector, Alignment
from kaa.colors import Color
from kaa.transitions import (
    NodeTransitionsSequence, NodeTransitionsParallel, NodeTransitionCallback,
    NodeTransitionDelay, NodeTransition,
)

from .constants import (
    LANE_HERO_SLOTS, SPRITE_SOAP_METER, SPRITE_LIQUID_SOAP,
    SPRITE_ANTIVIRUS, SPRITE_FRAMES_PEOPLE,
)
from .nodes import (
    SoapNode, OilRunner, MiniSoapRunner, VirusRunner,
    LiquidSoapRunner, AntivirusRunner, CounterStatusUINode
)


class EffectsManager:
    def __init__(self, *, root_node, camera):
        self.camera = camera
        self.flasher = root_node.add_child(
            Node(
                shape=Polygon.from_box(Vector(1400, 800)),
                color=Color(0., 0., 0., 0.),
                z_index=100,
            )
        )
        self.camera_shake_ticks = 0

    def flash(self):
        self.camera_shake_ticks = 15
        self.flasher.transition = [
            NodeTransition(
                Node.color, Color(1., 0., 0., 0.3), duration=200.,
            ),
            NodeTransition(
                Node.color, Color(0., 0., 0., 0.0), duration=100.,
            )
        ]

    def update_camera(self):
        if self.camera_shake_ticks:
            if self.camera_shake_ticks > 1:
                self.camera.position = Vector(
                    random.uniform(-10, 10),
                    random.uniform(-10, 10),
                )
            else:
                self.camera.position = Vector(0, 0)
            self.camera_shake_ticks -= 1

    def reset(self):
        self.camera_shake_ticks = 0
        self.camera.position = Vector(0, 0)


class RunnersManager:
    def __init__(self, *, space_node):
        self.space_node = space_node
        self.speed_mod = 0.
        self.slowdown_power = 0

        self.space_node.transitions_manager.set(
            'spawn_periodic', NodeTransitionsSequence(
                [
                    NodeTransitionDelay(200),
                    NodeTransitionCallback(lambda _: self.spawn_runner()),
                ], loops=0,
            )
        )
        self.space_node.transitions_manager.set(
            'update_speed_mod_periodic', NodeTransitionsSequence(
                [
                    NodeTransitionDelay(300),
                    NodeTransitionCallback(lambda _: self.update_speed_mod()),
                ], loops=0,
            )
        )

    def spawn_runner(self):
        speed_mod = self.speed_mod
        if random.random() > max(0.80 - self.speed_mod / 1000., 0.5):
            r = random.random()
            if r < 0.1:
                runner_cls = OilRunner
            elif r < 0.25:
                runner_cls = MiniSoapRunner
            elif r < 0.30:
                runner_cls = LiquidSoapRunner
            elif r < 0.35:
                runner_cls = AntivirusRunner
            else:
                runner_cls = VirusRunner
                if self.slowdown_power:
                    speed_mod *= 0.65 ** self.slowdown_power
            self.space_node.add_child(
                runner_cls(speed_mod=self.speed_mod, z_index=20)
            )

    def update_speed_mod(self):
        self.speed_mod += 1.5

    def nuke_enemies(self):
        for child_node in self.space_node.children:
            if isinstance(child_node, VirusRunner):
                child_node.handle_destruction()

    def slowdown_enemies(self):
        self.slowdown_power += 1
        for child_node in self.space_node.children:
            if isinstance(child_node, VirusRunner):
                child_node.slowdown(0.65)

        self.space_node.transitions_manager.set(
            'slowndown_cancel', NodeTransitionsSequence(
                [
                    NodeTransitionDelay(3000),
                    NodeTransitionCallback(lambda _: self._on_cancel_slowdown()),
                ],
            )
        )

    def _on_cancel_slowdown(self):
        self.slowdown_power = 0


class PowerupsManager:
    def __init__(self, *, player_state, runners_manager):
        self.player_state = player_state
        self.runners_manager = runners_manager

    def use_antivirus(self):
        if self.player_state.antivirus_powerup_counter > 0:
            self.player_state.antivirus_powerup_counter.decrease(1)
            self.runners_manager.nuke_enemies()

    def use_liquid_soap(self):
        if self.player_state.liquid_soap_powerup_counter > 0:
            self.player_state.liquid_soap_powerup_counter.decrease(1)
            self.runners_manager.slowdown_enemies()


class PlayerManager:
    def __init__(self, *, player_state, space_node, effects_manager):
        self.player_state = player_state
        self.space_node = space_node
        self.effects_manager = effects_manager
        self.soap = self.space_node.add_child(
            SoapNode(
                z_index=30,
            )
        )
        self.is_moving = False
        self.is_frozen = False
        self.current_lane = 2

    def kill(self):
        self.soap.transition = NodeTransitionsParallel([
            NodeTransition(Node.scale, Vector.xy(0.0), duration=1500),
            NodeTransition(Node.color, Color(1., 0., 0., 0.), duration=1500),
        ])
        self.soap.lifetime = 1500

    def handle_enemy_kill(self, enemy_node):
        self.player_state.score += 10

    def handle_enemy_missed(self, enemy_node):
        self.player_state.people_counter.decrease(1)
        self.effects_manager.flash()

    def handle_pickup_grab(self, pickup_node):
        if isinstance(pickup_node, OilRunner):
            if not self.is_frozen:
                self.is_frozen = True
                self.soap.transitions_manager.set(
                    'frozen',
                    NodeTransitionsSequence([
                        NodeTransition(Node.color, Color(0.5, 0.5, 0.5),
                                       duration=400., back_and_forth=True),
                        NodeTransitionCallback(self._on_end_frozen),
                    ])
                )
        elif isinstance(pickup_node, MiniSoapRunner):
            self.player_state.soap_meter_counter.increase(10000)
        elif isinstance(pickup_node, LiquidSoapRunner):
            self.player_state.liquid_soap_powerup_counter.increase(1)
        elif isinstance(pickup_node, AntivirusRunner):
            self.player_state.antivirus_powerup_counter.increase(1)

    def consume_fuel(self, dt: int):
        self.player_state.soap_meter_counter.decrease(dt)

    def move_lane(self, movement_dir: int):
        if (
                not self.is_moving
                and 0 <= self.current_lane + movement_dir < len(LANE_HERO_SLOTS)
                and not self.is_frozen
        ):
            self.is_moving = True
            self.current_lane += movement_dir
            self.soap.transitions_manager.set(
                'movement',
                NodeTransitionsSequence([
                    NodeTransition(Node.position,
                                   LANE_HERO_SLOTS[self.current_lane], duration=150.),
                    NodeTransitionCallback(self._on_end_movement),
                ]),
            )

    def _on_end_movement(self, _):
        self.is_moving = False

    def _on_end_frozen(self, _):
        self.is_frozen = False


class UIManager:
    def __init__(self, player_state, root_node):
        self.player_state = player_state
        self.ui_root = root_node.add_child(
            Node(
                position=Vector(0, 240),
            )
        )
        self.soap_meter = self.ui_root.add_child(
            Node(
                position=Vector(320, 20),
                origin_alignment=Alignment.left,
                sprite=SPRITE_SOAP_METER,
                z_index=50,
            )
        )

        self.soap_meter_label = self.ui_root.add_child(
            TextNode(
                # scale=Vector(1.1, 1),
                position=Vector(320, -15),
                origin_alignment=Alignment.top_left,
                font=Font('hope_in_soap/assets/Pixeled_0.ttf'),
                font_size=42.,
                text="Soap-o-meter",
                z_index=50,
            )
        )

        self.score = self.ui_root.add_child(
            TextNode(
                # scale=Vector(1.1, 1),
                position=Vector(-470, -15),
                origin_alignment=Alignment.top_left,
                font=Font('hope_in_soap/assets/Pixeled_0.ttf'),
                font_size=36.,
                text="Score: 123",
                z_index=50,
            )
        )

        self.liquid_soap_powerup_status = self.ui_root.add_child(
            CounterStatusUINode(
                position=Vector(450, -130),
                powerup_sprite=SPRITE_LIQUID_SOAP,
                max_count=3,
            )
        )

        self.antivirus_powerup_status = self.ui_root.add_child(
            CounterStatusUINode(
                position=Vector(530, -130),
                powerup_sprite=SPRITE_ANTIVIRUS,
                max_count=3,
            )
        )
        self.people_label = self.ui_root.add_child(
            TextNode(
                # scale=Vector(1.1, 1),
                position=Vector(-620, -15),
                origin_alignment=Alignment.top_left,
                font=Font('hope_in_soap/assets/Pixeled_0.ttf'),
                font_size=36.,
                text="People:",
                z_index=50,
            )
        )
        self.people_status = self.ui_root.add_child(
            CounterStatusUINode(
                position=Vector(-620, 10),
                powerup_sprite=SPRITE_FRAMES_PEOPLE,
                max_count=500,
                break_count=40,
                minor_sep=Vector(7, 0),
                major_sep=Vector(0, 12),
            )
        )

        self.game_over_background = root_node.add_child(
            Node(
                shape=Polygon.from_box(Vector(1400, 1000)),
                color=Color(0, 0, 0, 0),
                visible=False,
                z_index=150,
            )
        )
        self.game_over_text = self.game_over_background.add_child(
            TextNode(
                font_size=56.,
                font=Font('hope_in_soap/assets/Pixeled_0.ttf'),
                text="GAME OVER",
                color=Color(0, 0, 0, 0),
                z_index=151,
            )
        )

    def show_game_over(self):
        self.game_over_background.visible = True
        self.game_over_background.transition = NodeTransition(
            Node.color, Color(0, 0, 0, 0.8), duration=30000,
        )
        self.game_over_text.transition = NodeTransition(
            Node.color, Color(1, 1, 1, 1), duration=3000,
        )

    def update_ui(self):
        fuel_level = (
            int(self.player_state.soap_meter_counter)
            / self.player_state.soap_meter_counter.max_value
        )
        self.soap_meter.scale = Vector(
            x=fuel_level, y=1.
        )
        self.score.text = "Score: {}".format(self.player_state.score)
        self.liquid_soap_powerup_status.update_count(
            int(self.player_state.liquid_soap_powerup_counter)
        )
        self.antivirus_powerup_status.update_count(
            int(self.player_state.antivirus_powerup_counter)
        )
        self.people_status.update_count(
            int(int(self.player_state.people_counter) ** 2.5)
        )
