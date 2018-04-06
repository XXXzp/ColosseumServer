DEBUG_MATCH_INFO_EXAMPLE = {
    'gameID': '10112323123',  # just ID number
    'game': 'dealer_renju',  # name of the game
    'NPC': 'starter',  # 'False' 'starter' 'master' 'Godlike'
    'rounds': '100',
    'random_seed': 'False',  # 'False' 'int'
    'game_define': 'False',  # for poker game define file is required
    'players': [
        {'name_1': 'Alice'},
        {'name_2': 'Bob'}
    ]
}


REFEREE_RET_EXAMPLE = {
    'status': 'success',  # Task.STATUS  and   'game no exist'
    'score': 'SCORE:47|53:a|b'  # False if game is no success
}


RESULT = {
    'status': 'ongoing',
    'score': 'False',
    'xxx': 12312
}