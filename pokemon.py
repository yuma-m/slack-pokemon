#!/usr/bin/env python3
import os
import pathlib
import csv
import random
import time
import traceback
from collections import defaultdict
from typing import Dict, Set

from attr import attrs, attrib
from slackclient import SlackClient

TOKEN = os.getenv("SLACK_TOKEN")
CHANNEL = os.getenv("SLACK_CHANNEL")
USERNAME = os.getenv("SLACK_USERNAME")
ICON = os.getenv("SLACK_ICON")


@attrs
class Pokemon:
    id_ = attrib()
    name = attrib()
    yomi = attrib()
    name_en = attrib()
    h = attrib()
    a = attrib()
    b = attrib()
    c = attrib()
    d = attrib()
    s = attrib()
    sum_ = attrib()
    type1 = attrib()
    type2 = attrib()
    height = attrib()
    weight = attrib()

    @property
    def explanation(self):
        type_ = self.type1 if not self.type2 else f"{self.type1}/{self.type2}"
        msg = f"{self.name}は、{type_}タイプのポケモンで、全国図鑑番号は{self.id_}。\n" \
              f"高さ{self.height}m、重さ{self.weight}kgだよ。"
        return msg


def load_pokemons():
    path = pathlib.Path(__file__).parent / "pokemon.csv"
    pokemons = {}
    with open(path) as f:
        reader = csv.reader(f)
        for row in reader:
            pokemon = Pokemon(*row)
            pokemons[pokemon.name] = pokemon
    return pokemons


def order_by_initial(pokemons):
    initials = defaultdict(set)
    for pokemon in pokemons:
        initials[pokemon.yomi[:1]].add(pokemon.name)
    return initials


class PokemonSlack:
    def __init__(self):
        self._pokemons: Dict[str, Pokemon] = load_pokemons()
        self._pokemon_by_initial: Dict[str, Set[str]] = order_by_initial(self._pokemons.values())
        self._used = set()
        self._last_pokemon = ""
        self.client = SlackClient(TOKEN)

    def _choose_candidate(self, initial):
        candidates = list(self._pokemon_by_initial[initial])
        random.shuffle(candidates)
        for pokemon in candidates:
            if not pokemon.endswith("ン") and pokemon not in self._used:
                return pokemon
        return None

    def _generate_reply(self, message):
        if message.find("降参") >= 0:
            self._used.clear()
            return "お疲れ様でした！"
        if message not in self._pokemons:
            return
        if message.endswith("ン"):
            self._used.clear()
            return "ン で終わったからキミの負け！"
        if self._used and not message.startswith(self._last_pokemon.yomi[-1:]):
            return f"しりとりになっていないよ: {self._last_pokemon.name} の {self._last_pokemon.yomi[-1:]} から始めてね"
        if message in self._used:
            self._used.clear()
            return f"{message} はもう使ったからキミの負け！"
        self._used.add(message)
        current = self._pokemons[message]
        candidate = self._choose_candidate(current.yomi[-1:])
        if not candidate:
            self._used.clear()
            return "降参しました"
        self._used.add(candidate)
        self._last_pokemon = self._pokemons[candidate]
        explanation = current.explanation
        return f"{explanation}\n\n次は・・・ {candidate}！"

    def _send_reply(self, message):
        self.client.api_call("chat.postMessage", text=message, channel=CHANNEL,
                             username=USERNAME, icon_emoji=ICON)

    @staticmethod
    def _get_text(message):
        u""" メッセージからテキストを取得 """
        if message.get('type') != u'message':
            return ""

        sub_type = message.get('subtype')
        if not sub_type:
            return message["text"]
        return ""

    def _handle_message(self, message):
        u""" メッセージが届いた際のメイン処理 """
        text = self._get_text(message)
        if text:
            print(f"received: {text}")
            reply = self._generate_reply(text)
            if reply:
                print(f"reply: {reply}")
                self._send_reply(reply)

    def _update(self):
        messages = self.client.rtm_read()
        for message in messages:
            try:
                self._handle_message(message)
            except:
                print(message)
                print(traceback.format_exc())

    def run(self):
        if not self.client.rtm_connect():
            print('Connection Failed, invalid token?')
            return
        self.client.api_call("users.setActive")
        print("Begin main loop")
        while True:
            self._update()
            time.sleep(0.1)


def main():
    pokemon = PokemonSlack()
    pokemon.run()


if __name__ == '__main__':
    main()
