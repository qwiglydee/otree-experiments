import time
import random
from otree.api import *
from otree import settings

from .images import generate_image, encode_image


doc = """
Counting symbols in a matrix
"""


class Constants(BaseConstants):
    name_in_url = "matrices"
    players_per_group = None
    num_rounds = 1

    matrix_w = 5
    matrix_h = 4
    characters = "←↓"
    counted_char = "←"


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # current state of the game
    # for multi-round games: increment the round and reset iteration
    game_round = models.IntegerField(initial=0)
    game_iteration = models.IntegerField(initial=0)

    # stats are updated after game round, in before_next_page
    total = models.IntegerField(initial=0)
    correct = models.IntegerField(initial=0)
    incorrect = models.IntegerField(initial=0)


# puzzle-specific stuff


class Puzzle(ExtraModel):
    """A model to keep record of all generated puzzles"""

    player = models.Link(Player)
    round = models.IntegerField(initial=0)
    iteration = models.IntegerField(initial=0)
    timestamp = models.FloatField(initial=0)

    content = models.StringField()
    solution = models.IntegerField()

    # the following fields remain null for unanswered puzzles
    response_timestamp = models.FloatField()
    answer = models.IntegerField()
    is_correct = models.BooleanField()
    retries = models.IntegerField(initial=0)


def generate_puzzle(player: Player) -> Puzzle:
    """Create new puzzle for a player"""
    w = Constants.matrix_w
    h = Constants.matrix_h
    length = w * h
    content = "".join((random.choice(Constants.characters) for i in range(length)))
    count = content.count(Constants.counted_char)
    return Puzzle.create(player=player, content=content, solution=count,)


def encode_puzzle(puzzle: Puzzle):
    """Create an image for a puzzle"""
    image = generate_image((Constants.matrix_w, Constants.matrix_h), puzzle.content)
    data = encode_image(image)
    return data


def get_last_puzzle(player):
    """Get last (current) puzzle for a player"""
    puzzles = Puzzle.filter(
        player=player, round=player.game_round, iteration=player.game_iteration
    )
    if puzzles:
        return puzzles[-1]


def check_answer(puzzle: Puzzle, answer: str):
    """Check given answer for a puzzle and update its status"""
    if answer == "" or answer is None:
        raise ValueError("Unexpected empty answer from client")
    puzzle.answer = answer
    puzzle.is_correct = int(answer) == puzzle.solution


def summarize_puzzles(player: Player):
    """Returns summary stats for a player

    Used to provide info for client, and to update player after a game round
    """
    total = len(Puzzle.filter(player=player))
    correct = len(Puzzle.filter(player=player, is_correct=True))
    incorrect = len(Puzzle.filter(player=player, is_correct=False))
    return {
        'total': total,
        'correct': correct,
        'incorrect': incorrect,
    }


# gameplay logic


def play_game(player: Player, data: dict):
    """Handles iterations of the game on a live page

    Messages:
    - client > server {} -- empty message means page reload
    - server < client {'next': true} -- request for next (or first) puzzle
    - server > client {'image': data, 'stats': ...} -- puzzle image
    - server < client {'answer': data} -- answer to a puzzle
    - server > client {'feedback': true|false, 'stats': ...} -- feedback on the answer
    - server > client {'gameover': true} -- all iterations played
    if DEBUG=1
    - server < client {'cheat': true} -- request solution
    - server > client {'solution': str} -- solution
    """
    conf = player.session.config
    puzzle_delay = conf.get('puzzle_delay', 1.0)
    retry_delay = conf.get('retry_delay', 1.0)
    force_solve = conf.get('force_solve', False)
    allow_retry = conf.get('allow_retry', False) or force_solve
    max_iter = conf.get('max_iterations', 0)

    now = time.time()

    # get last puzzle, if any
    last = get_last_puzzle(player)

    if data == {}:
        if last:  # reloaded in middle of round, return current puzzle
            stats = summarize_puzzles(player)
            data = encode_puzzle(last)
            return {player.id_in_group: {"image": data, "stats": stats}}
        else:  # initial load, generate first puzzle
            puzzle = generate_puzzle(player)
            puzzle.timestamp = now
            puzzle.iteration = 1
            player.game_iteration = 1
            stats = summarize_puzzles(player)
            data = encode_puzzle(puzzle)
            return {player.id_in_group: {"image": data, "stats": stats}}

    # generate next puzzle and return image
    if "next" in data:
        if not last:
            raise RuntimeError("Missing current puzzle!")
        if now - last.timestamp < puzzle_delay:
            raise RuntimeError("Client advancing too fast!")
        if force_solve and last.is_correct is not True:
            raise RuntimeError("Attempted to skip unsolved puzzle!")
        if last.answer is None:
            raise RuntimeError("Attempted to skip unanswered puzzle!")
        if max_iter and last.iteration >= max_iter:
            return {player.id_in_group: {"gameover": True}}

        # new puzzle
        puzzle = generate_puzzle(player)
        puzzle.timestamp = now
        puzzle.iteration = last.iteration + 1 if last else 1
        player.game_iteration = puzzle.iteration

        # get total counters
        stats = summarize_puzzles(player)

        # return image
        data = encode_puzzle(puzzle)
        return {player.id_in_group: {"image": data, "stats": stats}}

    # check given answer and return feedback
    if "answer" in data:
        if not last:
            raise RuntimeError("Missing current puzzle")
        if last.answer is not None:  # retrying
            if not allow_retry:
                raise RuntimeError("Client retries the same puzzle!")
            if now - last.response_timestamp < retry_delay:
                raise RuntimeError("Client retrying too fast!")

        check_answer(last, data["answer"])
        last.response_timestamp = now
        last.retries += 1

        # get total counters
        stats = summarize_puzzles(player)

        # return feedback
        return {player.id_in_group: {'feedback': last.is_correct, 'stats': stats}}

    if "cheat" in data and settings.DEBUG:
        if not last:
            raise RuntimeError("Missing current puzzle")
        return {player.id_in_group: {'solution': last.solution}}

    # otherwise
    raise ValueError("Invalid message from client!")



class Game(Page):
    timeout_seconds = 60
    live_method = play_game

    @staticmethod
    def vars_for_template(player: Player):
        session = player.session

        return dict(DEBUG=settings.DEBUG,)

    @staticmethod
    def js_vars(player: Player):
        conf = player.session.config
        return dict(
            puzzle_delay=conf.get('puzzle_delay', 1.0),
            retry_delay=conf.get('retry_delay', 1.0),
            force_solve=conf.get('force_solve', False),
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        stats = summarize_puzzles(player)
        player.total = stats['total']
        player.correct = stats['correct']
        player.incorrect = stats['incorrect']


class Results(Page):
    pass


page_sequence = [Game, Results]
