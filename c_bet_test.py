def calculate_c_bet(data):
    original_raiser = None
    flop_reached = False
    c_bet_made = False
    c_bet_count = 0
    flop_count = 0

    for event in data['events']:
        payload = event['payload']
        if payload['type'] == 8 and not original_raiser:  # Original raiser in pre-flop
            original_raiser = payload['seat']
        elif payload['type'] == 9 and payload['turn'] == 1:  # Flop reached
            flop_reached = True
            if original_raiser:
                flop_count += 1
        elif flop_reached and payload['type'] == 8 and payload['seat'] == original_raiser:  # C-bet made
            c_bet_made = True

    if c_bet_made:
        c_bet_count += 1

    if flop_count > 0:
        c_bet_percentage = (c_bet_count / flop_count) * 100
    else:
        c_bet_percentage = 0

    return c_bet_percentage

def main():
    test_data = {
        "events": [
            {"payload": {"type": 8, "seat": 3}},  # Original raiser in pre-flop
            {"payload": {"type": 9, "turn": 1}},  # Flop reached
            {"payload": {"type": 8, "seat": 3}},  # C-bet made by original raiser
            {"payload": {"type": 9, "turn": 2}},  # Turn reached
            {"payload": {"type": 8, "seat": 3}},  # Bet made by original raiser
            {"payload": {"type": 9, "turn": 3}},  # River reached
        ]
    }

    print(calculate_c_bet(test_data))  # Should print 100.0

if __name__ == "__main__":
    main()