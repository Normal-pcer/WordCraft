import json
import math
from time import perf_counter
from typing import List, Tuple

import pygame

from entity import Player
from util import Identifier, Vector2, Read, Debug
from world import World

_cache_texture = {}


class WorldRenderer:
    """
    wordcraft.client.WorldRenderer
    Rendering objects (blocks, entities, etc.) in the world on game window.
    """

    gameWindow = pygame.Surface
    relativePlayer: Player
    runningSave: World
    fontSize = 60
    tmp = list()

    class BlockTexture:
        """
        wordcraft.client.WorldRenderer.BlockTexture
        """

        character: str
        color: Tuple[int, int, int]
        font: pygame.font.Font
        selected: bool
        fontSize: int

        def __init__(self, character: str, color: Tuple[int, int, int],
                     font="Microsoft YaHei", selected=False, font_size=60):
            self.character = character
            self.color = color
            self.font = pygame.font.SysFont(font, font_size)
            self.selected = selected
            self.fontSize = font_size

        @classmethod
        def get_block_texture(cls, identifier: Identifier,
                              default=("材质丢失", (0, 0, 0))):
            """
            Get a block texture object by the given identifier.
            default: Return when unable to find the texture file, etc.
            """
            if str(identifier) in _cache_texture:
                return _cache_texture[str(identifier)]

            textures_index_file = Read.read_str(
                "textures/index.json", default=lambda e: Debug.Log.warning(
                    "Exception while reading textures index: " + repr(e)))
            if textures_index_file is not None:
                textures_index = json.loads(textures_index_file)

                for texture_pack in textures_index:
                    block_json_file = Read.read_str(
                        f"textures/{texture_pack}/{identifier.namespace}/blocks/blocks.json")
                    if block_json_file is not None:
                        blocks_texture_dict = json.loads(block_json_file)
                        if identifier.path in blocks_texture_dict:
                            _cache_texture[str(identifier)] = (
                                cls(*blocks_texture_dict[identifier.path]))
                            return cls(*blocks_texture_dict[identifier.path])

        def blit(self, window: pygame.surface.Surface, destination: tuple):
            window.blit(self.font.render(self.character,
                                         True, self.color), destination)
            if self.selected:
                pygame.draw.rect(window, (0, 0, 0), (
                    destination[0], destination[1] + 15, self.fontSize,
                    self.fontSize), 2)

    class EntityTexture:

        characters: List[str]
        color: Tuple[int]
        font: pygame.font.Font
        fontSize: int

        def __init__(self, characters: List[str], color: Tuple[int], font="Microsoft YaHei",
                     font_size=60):
            self.characters = characters
            self.color = color
            self.font = pygame.font.SysFont(font, font_size)
            self.fontSize = font_size
            ...

        @classmethod
        def get_entity_texture(cls, identifier: Identifier,
                               default=(["〇"], (0, 0, 0))):
            """
            Get an entity texture object by the given identifier.
            default: Return when unable to find the texture file, etc.
            """

            if str(identifier) in _cache_texture:
                return _cache_texture[str(identifier)]

            textures_index_file = Read.read_str(
                "textures/index.json", default=lambda e: Debug.Log.warning(
                    "Exception while reading textures index: " + repr(e)))
            if textures_index_file is not None:
                textures_index = json.loads(textures_index_file)

                for texture_pack in textures_index:
                    block_json_file = Read.read_str(
                        f"textures/{texture_pack}/{identifier.namespace}/entities/entities.json")
                    if block_json_file is not None:
                        blocks_texture_dict = json.loads(block_json_file)
                        if identifier.path in blocks_texture_dict:
                            _cache_texture[str(identifier)] = (
                                cls(*blocks_texture_dict[identifier.path]))
                            return cls(*blocks_texture_dict[identifier.path])

        def blit(self, window: pygame.surface.Surface, destination: Vector2) -> None:
            for y_block in range(len(self.characters)):
                for x_block in range(len(self.characters[y_block])):
                    element = self.characters[y_block][x_block]
                    p_x = destination.x + self.fontSize * x_block
                    p_y = destination.y + self.fontSize * y_block
                    window.blit(self.font.render(element, True, self.color),
                                (p_x, p_y))

    def __init__(self, game_window: pygame.Surface, running_save: World,
                 player: Player):
        self.gameWindow = game_window
        self.runningSave = running_save
        self.relativePlayer = player

    def frame(self):
        # Calculate grid size required
        width, height = self.gameWindow.get_size()
        half_width = (width - self.fontSize) / 2
        quarter_height = (height - self.fontSize) / 4

        player_to_left_blocks = math.ceil(half_width / self.fontSize) + 1
        player_to_right_blocks = math.ceil(half_width / self.fontSize) + 1
        player_to_bottom_blocks = math.ceil(quarter_height / self.fontSize) + 1
        player_to_top_blocks = math.ceil(
            quarter_height * 3 / self.fontSize) + 1

        player_feet_in_screen_x = half_width - self.fontSize / 2
        player_feet_in_screen_y = quarter_height * 3 - self.fontSize / 2

        current_time = perf_counter()
        pass_time = current_time - self.runningSave.lastTickTime
        player_feet_x = (self.relativePlayer.playerEntity.position.x +
                         self.relativePlayer.playerEntity.speed.x * pass_time)
        player_feet_y = (self.relativePlayer.playerEntity.position.y +
                         self.relativePlayer.playerEntity.speed.y * pass_time)

        grid = self.runningSave.get_blocks(
            int(player_feet_x - player_to_left_blocks), int(player_feet_x + player_to_right_blocks),
            int(player_feet_y - player_to_bottom_blocks), int(player_feet_y + player_to_top_blocks))

        grid = grid[::-1]

        screen_y = (player_feet_in_screen_y - self.fontSize *
                    (player_to_top_blocks - 1 - (player_feet_y - int(player_feet_y))))
        screen_x = (player_feet_in_screen_x - self.fontSize *
                    (player_to_left_blocks - (player_feet_x - int(player_feet_x))))

        self.tmp.append(self.runningSave.get_block(-5, 3).blockId)
        if self.tmp.__len__() > 2 and str(self.tmp[-1]) != str(self.tmp[-2]):
            print(self.tmp[-1], self.tmp[-2])
            debugger = True

        for blocks_y in range(len(grid)):
            for blocks_x in range(len(grid[0])):
                mouse_pos = pygame.mouse.get_pos()
                texture = self.BlockTexture.get_block_texture(
                    grid[blocks_y][blocks_x].blockId)
                if (pygame.mouse.get_focused() and
                        screen_x <= mouse_pos[0] < screen_x + self.fontSize and
                        screen_y <= mouse_pos[1] - 15 < screen_y + self.fontSize):
                    texture.selected = True
                    (self.BlockTexture(str((
                        int(player_feet_x - player_to_left_blocks) + blocks_x,
                        int(player_feet_y + player_to_top_blocks) - blocks_y)), (0, 0, 0))
                     .blit(self.gameWindow, (0, 30)))
                    if pygame.mouse.get_pressed()[0]:
                        print(pygame.mouse.get_pressed())
                        self.runningSave.remove_block(
                            int(player_feet_x - player_to_left_blocks) + blocks_x,
                            int(player_feet_y + player_to_top_blocks) - blocks_y)
                else:
                    texture.selected = False
                texture.blit(self.gameWindow, (screen_x, screen_y))
                screen_x += self.fontSize
            screen_x = (player_feet_in_screen_x - self.fontSize * player_to_left_blocks -
                        (player_feet_x - int(player_feet_x)) * self.fontSize)
            screen_y += self.fontSize

        player_texture = self.EntityTexture.get_entity_texture(
            self.relativePlayer.playerEntity.typeId)
        player_texture.blit(self.gameWindow,
                            Vector2(player_feet_in_screen_x, player_feet_in_screen_y))
