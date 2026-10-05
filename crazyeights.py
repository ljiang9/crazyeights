#!/usr/bin/env python3
"""疯狂八点 (Crazy Eights) —— 终端纸牌游戏,你 vs 电脑。

规则:
- 52 张牌,每人发 5 张,其余为牌堆;弃牌堆顶第一张为当前牌。
- 出牌必须与当前牌同花色或同点数;"8" 是万能牌,打出时自选花色。
- 无牌可出则从牌堆摸一张;牌堆摸空则把弃牌堆(除顶牌)洗匀重做牌堆。
- 先出完手牌者获胜。
"""

import argparse
import random
import secrets
import sys

SUITS = ["♠", "♥", "♦", "♣"]
SUIT_NAME = {"♠": "黑桃", "♥": "红桃", "♦": "方块", "♣": "梅花"}
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


def new_deck():
    return [(r, s) for s in SUITS for r in RANKS]


def card_name(card):
    r, s = card
    return f"{SUIT_NAME[s]}{r}"


def is_legal(card, top, active_suit):
    """card 能否压在 top 上。active_suit 是 8 指定的当前有效花色。"""
    r, s = card
    if r == "8":
        return True
    tr, ts = top
    eff_suit = active_suit if tr == "8" else ts
    return r == tr or s == eff_suit


def ai_choose(hand, top, active_suit):
    """电脑策略:首张合法牌;8 留到只有它能出时再打(简单策略,已文档化)。"""
    non8 = [c for c in hand if c[0] != "8" and is_legal(c, top, active_suit)]
    if non8:
        return non8[0]
    eights = [c for c in hand if c[0] == "8"]
    if eights:
        return eights[0]
    return None


def ai_suit(hand):
    """打出 8 后选花色:手中最多的花色。"""
    counts = {s: 0 for s in SUITS}
    for r, s in hand:
        if r != "8":
            counts[s] += 1
    return max(SUITS, key=lambda s: counts[s])


class Game:
    def __init__(self, rng):
        self.rng = rng
        deck = new_deck()
        rng.shuffle(deck)
        self.deck = deck
        self.you = [self._draw() for _ in range(5)]
        self.ai = [self._draw() for _ in range(5)]
        self.discard = [self._draw()]
        while self.discard[0][0] == "8":
            # 首张是 8 则埋回牌堆重抽,避免开局万能
            self.deck.append(self.discard.pop())
            rng.shuffle(self.deck)
            self.discard = [self._draw()]
        self.active_suit = None
        self.turn = "you"

    def _draw(self):
        if not self.deck:
            top = self.discard.pop()
            self.deck = self.discard
            self.discard = [top]
            self.rng.shuffle(self.deck)
            if not self.deck:
                return None
        return self.deck.pop()

    def top(self):
        return self.discard[-1]

    def legal_moves(self, hand):
        top = self.top()
        return [c for c in hand if is_legal(c, top, self.active_suit)]

    def play(self, hand, card, new_suit=None):
        hand.remove(card)
        self.discard.append(card)
        self.active_suit = new_suit if card[0] == "8" else None
        return len(hand) == 0

    def status(self):
        t = self.top()
        eff = self.active_suit if t[0] == "8" else t[1]
        return (f"当前牌: {card_name(t)}"
                + (f" (指定花色: {SUIT_NAME[eff]})" if t[0] == "8" else "")
                + f" | 你 {len(self.you)} 张, 电脑 {len(self.ai)} 张")


def play_interactive(seed=None):
    if not sys.stdin.isatty():
        print("error: 交互模式需要终端,请用 --auto 自动对战。", file=sys.stderr)
        return 2
    rng = random.Random(seed) if seed is not None else random.Random(secrets.randbits(64))
    g = Game(rng)
    print("疯狂八点:你 vs 电脑,先出完手牌者胜。出牌规则:同花色/同点数,8 为万能牌。")
    print("输入如 `红桃8` 或序号出牌;`摸` 摸牌;`q` 退出。")
    while True:
        print("\n" + g.status())
        if g.turn == "you":
            print("你的手牌:", " ".join(f"{i+1}:{card_name(c)}" for i, c in enumerate(g.you)))
            legal = g.legal_moves(g.you)
            if not legal:
                c = g._draw()
                if c is None:
                    print("牌堆和弃牌堆都空了,平局。")
                    return 0
                g.you.append(c)
                print(f"无牌可出,摸到 {card_name(c)}。")
                g.turn = "ai"
                continue
            raw = input("出牌> ").strip()
            if raw.lower() == "q":
                print("已退出。")
                return 0
            if raw == "摸":
                c = g._draw()
                if c is None:
                    print("牌堆和弃牌堆都空了,平局。")
                    return 0
                g.you.append(c)
                print(f"摸到 {card_name(c)}。")
                g.turn = "ai"
                continue
            card = None
            for c in g.you:
                if card_name(c) == raw:
                    card = c
                    break
            if card is None and raw.isdigit() and 1 <= int(raw) <= len(g.you):
                card = g.you[int(raw) - 1]
            if card is None or not is_legal(card, g.top(), g.active_suit):
                print("非法出牌,请出同花色/同点数的牌,8 随时可出。")
                continue
            new_suit = None
            if card[0] == "8":
                s = input("8 万能!指定花色(黑桃/红桃/方块/梅花)> ").strip()
                m = {"黑桃": "♠", "红桃": "♥", "方块": "♦", "梅花": "♣"}
                new_suit = m.get(s, max(SUITS, key=lambda x: sum(1 for _, ss in g.you if ss == x)))
            if g.play(g.you, card, new_suit):
                print("🎉 你赢了!")
                return 0
            print(f"你打出 {card_name(card)}。")
            g.turn = "ai"
        else:
            legal = g.legal_moves(g.ai)
            if not legal:
                c = g._draw()
                if c is None:
                    print("牌堆和弃牌堆都空了,平局。")
                    return 0
                g.ai.append(c)
                g.turn = "you"
                continue
            card = ai_choose(g.ai, g.top(), g.active_suit)
            new_suit = ai_suit(g.ai) if card[0] == "8" else None
            if g.play(g.ai, card, new_suit):
                print("电脑出完了,电脑获胜。")
                return 0
            print(f"电脑打出 {card_name(card)}"
                  + (f",指定 {SUIT_NAME[new_suit]}" if new_suit else "") + "。")
            g.turn = "you"


def play_auto(seed=None):
    rng = random.Random(seed) if seed is not None else random.Random(secrets.randbits(64))
    g = Game(rng)
    rounds = 0
    while rounds < 10000:
        rounds += 1
        hand = g.you if g.turn == "you" else g.ai
        legal = g.legal_moves(hand)
        if not legal:
            c = g._draw()
            if c is None:
                return "draw", rounds
            hand.append(c)
        else:
            if g.turn == "you":
                card = legal[0]
                new_suit = ai_suit(hand) if card[0] == "8" else None
            else:
                card = ai_choose(hand, g.top(), g.active_suit)
                # 断言:AI 永不出非法牌
                assert card is not None and is_legal(card, g.top(), g.active_suit), \
                    f"AI 非法出牌 {card_name(card)}"
                new_suit = ai_suit(hand) if card[0] == "8" else None
            if g.play(hand, card, new_suit):
                return g.turn, rounds
        g.turn = "ai" if g.turn == "you" else "you"
    return "draw", rounds


def main(argv=None):
    ap = argparse.ArgumentParser(description="疯狂八点:终端纸牌游戏,你 vs 电脑。")
    ap.add_argument("--auto", action="store_true", help="自动对战一局(双方都用简单策略)")
    ap.add_argument("--seed", type=int, default=None, help="随机种子")
    args = ap.parse_args(argv)
    if args.auto:
        winner, rounds = play_auto(args.seed)
        print(f"自动对战结束:获胜者={winner}, 回合数={rounds}")
        return 0
    return play_interactive(args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
