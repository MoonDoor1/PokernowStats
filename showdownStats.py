import json
import os

def calculate_showdown_percentage(data):
    player_stats = {}

    for hand in data['hands']:
        flop_seen = False
        players_in_hand = set()

        # Create a mapping of seat numbers to player names for this hand
        seat_to_name = {player['seat']: player['name'].lower() for player in hand['players']}

        for event in hand['events']:
            payload = event['payload']
            action_type = payload['type']
            player_seat = payload.get('seat', None)

            # Mark the flop event
            if 'turn' in payload and payload['turn'] == 1:
                flop_seen = True

            # Initialize player stats if player_seat exists
            if player_seat:
                player_name = seat_to_name[player_seat]

                if player_name not in player_stats:
                    player_stats[player_name] = {
                        'showdown_count': 0, 'hands_played': 0
                    }

                # Track players who've folded
                if action_type == 11:
                    if player_name in players_in_hand:
                        players_in_hand.remove(player_name)

                players_in_hand.add(player_name)

        # Increment the showdown count for players involved in a showdown
        if action_type == 15 and len(players_in_hand) > 1:
            for player in players_in_hand:
                player_stats[player]['showdown_count'] += 1

        # Increment the hands played for the players involved
        for player in players_in_hand:
            if flop_seen:
                player_stats[player]['hands_played'] += 1

    # Calculating final showdown percentage
    for player_name, stats in player_stats.items():
        if stats['hands_played'] > 0:  # Avoid division by zero
            stats['Showdown Percentage'] = round(stats['showdown_count'] / stats['hands_played'] * 100, 2)
        else:
            stats['Showdown Percentage'] = 0.0
            print("showdown percentage is zero")

    return player_stats

def main():
    directory = 'Poker Hands/JSON Data'
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            with open(os.path.join(directory, filename)) as f:
                data = json.load(f)
                stats = calculate_showdown_percentage(data)
                for player, data in stats.items():
                    print(f"Player {player}:")
                    print(f"Showdown count: {data['showdown_count']}")
                    print(f"Hands played: {data['hands_played']}")
                    print(f"Showdown percentage: {data['Showdown Percentage']}%")
                    print()

if __name__ == "__main__":
    main()