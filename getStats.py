import json
import pandas as pd
import os

def calculate_pnl(csv_filepath):
    # Read the CSV file
    df = pd.read_csv(csv_filepath)

    # Convert the player_nickname to lowercase
    df['player_nickname'] = df['player_nickname'].str.lower()

    # Convert the net for each player to the correct format
    df['net'] = df['net'] / 100  # Divide by 100 to move the decimal point

    # Group by player_nickname and sum the net
    pnl = df.groupby('player_nickname')['net'].sum()

    return pnl.to_dict()

def calculate_bb_per_100_hands(pnl_stats, hands_played_stats, big_blind):
    bb_per_100_hands_stats = {}

    for player_name in pnl_stats.keys():
        pnl = pnl_stats[player_name]
        hands_played = hands_played_stats.get(player_name, 1)  # Avoid division by zero

        # Calculate the number of big blinds won
        loss_per_hand = pnl / hands_played

        # Calculate the number of big blinds won per 100 hands
        bb_per_100_hands = (loss_per_hand * 100 ) * big_blind
        

        # Round to the nearest second decimal point
        bb_per_100_hands = round(bb_per_100_hands, 2)

        bb_per_100_hands_stats[player_name] = bb_per_100_hands

    return bb_per_100_hands_stats


def calculate_vpip(data):
    player_stats = {}

    for hand in data['hands']:
        flop_seen = False
        vpip_players = set()  # Players who've voluntarily put money in pot in this hand
        players_in_hand = set()  # Players who've played in this hand

        # Create a mapping of seat numbers to player names for this hand
        # Create a mapping of seat numbers to player names for this hand
        seat_to_name = {player['seat']: player['name'].lower() for player in hand['players']}

        for event in hand['events']:
            payload = event['payload']
            action_type = payload['type']
            player_seat = payload.get('seat', None)
            
            # Mark the flop event
            if 'turn' in payload and payload['turn'] == 1:  # Flop
                flop_seen = True

            # Initialize player stats if player_seat exists
            if player_seat:
                player_name = seat_to_name[player_seat]

                if player_name not in player_stats:
                    player_stats[player_name] = {
                        'VPIP_count': 0, 'hands_played': 0
                    }

                # Track VPIP
                if not flop_seen and action_type in [7, 8]:  # Raise or Call before flop
                    vpip_players.add(player_name)

                players_in_hand.add(player_name)

        # Increment the VPIP for the players involved
        for player in vpip_players:
            player_stats[player]['VPIP_count'] += 1

        # Increment the hands played for the players involved
        for player in players_in_hand:
            player_stats[player]['hands_played'] += 1
    
    # Calculating final VPIP percentage
   # Calculating final VPIP percentage
    for player_name, stats in player_stats.items():
        stats['VPIP'] = round(stats['VPIP_count'] / stats['hands_played'] * 100, 2)
        del stats['VPIP_count']  # Remove the count after calculating the percentage

    return player_stats

def calculate_pfr(data):
    player_stats = {}

    for hand in data['hands']:
        flop_seen = False
        pfr_players = set()  # Players who've raised before the flop in this hand
        players_in_hand = set()  # Players who've played in this hand

        # Create a mapping of seat numbers to player names for this hand
        seat_to_name = {player['seat']: player['name'].lower() for player in hand['players']}

        for event in hand['events']:
            payload = event['payload']
            action_type = payload['type']
            player_seat = payload.get('seat', None)
            
            # Mark the flop event
            if 'turn' in payload and payload['turn'] == 1:  # Flop
                flop_seen = True

            # Initialize player stats if player_seat exists
            if player_seat:
                player_name = seat_to_name[player_seat]

                if player_name not in player_stats:
                    player_stats[player_name] = {
                        'PFR_count': 0, 'hands_played': 0
                    }

                # Track PFR
                if not flop_seen and action_type == 8:  # Raise before flop
                    pfr_players.add(player_name)

                players_in_hand.add(player_name)

        # Increment the PFR for the players involved
        for player in pfr_players:
            player_stats[player]['PFR_count'] += 1

        # Increment the hands played for the players involved
        for player in players_in_hand:
            player_stats[player]['hands_played'] += 1
    
    # Calculating final PFR percentage
    for player_name, stats in player_stats.items():
        stats['PFR'] = round(stats['PFR_count'] / stats['hands_played'] * 100, 2)
        del stats['PFR_count']  # Remove the count after calculating the percentage

    return player_stats

def calculate_agg(data):
    player_stats = {}

    for hand in data['hands']:
        flop_seen = False
        agg_players = set()  # Players who've bet or raised after the flop in this hand
        players_in_hand = set()  # Players who've played in this hand

        # Create a mapping of seat numbers to player names for this hand
        seat_to_name = {player['seat']: player['name'].lower() for player in hand['players']}

        for event in hand['events']:
            payload = event['payload']
            action_type = payload['type']
            player_seat = payload.get('seat', None)
            
            # Mark the flop event
            if 'turn' in payload and payload['turn'] == 1:  # Flop
                flop_seen = True

            # Initialize player stats if player_seat exists
            if player_seat:
                player_name = seat_to_name[player_seat]

                if player_name not in player_stats:
                    player_stats[player_name] = {
                        'Agg_count': 0, 'hands_played': 0
                    }

                # Track Agg
                if flop_seen and action_type in [7, 8]:  # Bet or Raise after flop
                    agg_players.add(player_name)

                players_in_hand.add(player_name)

        # Increment the Agg for the players involved
        for player in agg_players:
            player_stats[player]['Agg_count'] += 1

        # Increment the hands played for the players involved
        for player in players_in_hand:
            player_stats[player]['hands_played'] += 1
    
    # Calculating final Agg percentage
    for player_name, stats in player_stats.items():
        stats['Agg'] = round(stats['Agg_count'] / stats['hands_played'] * 100, 2)
        del stats['Agg_count']  # Remove the count after calculating the percentage

    return player_stats

def calculate_c_bet(data):
    player_stats = {}

    for hand in data['hands']:
        flop_seen = False
        pre_flop_raiser = None
        c_bet_made = False  # Flag to track if a C-bet has been made in this hand
        players_in_hand = set()  # Players who've played in this hand

        # Create a mapping of seat numbers to player names for this hand
        seat_to_name = {player['seat']: player['name'].lower() for player in hand['players']}

        for event in hand['events']:
            payload = event['payload']
            action_type = payload['type']
            player_seat = payload.get('seat', None)

            # Mark the flop event
            if 'turn' in payload and payload['turn'] == 1:  # Flop
                flop_seen = True

            # Initialize player stats if player_seat exists
            if player_seat:
                player_name = seat_to_name[player_seat]

                if player_name not in player_stats:
                    player_stats[player_name] = {
                        'C_bet_count': 0, 'pre_flop_raise_count': 0, 'hands_played': 0
                    }

                # Track the pre-flop raiser
                if not flop_seen and action_type == 8:  # Raise before flop
                    if pre_flop_raiser is None:
                        pre_flop_raiser = player_name
                    player_stats[player_name]['pre_flop_raise_count'] += 1

                # Track C-bet
                if flop_seen and action_type == 8 and player_name == pre_flop_raiser and not c_bet_made:  # Bet after flop by pre-flop raiser
                    player_stats[player_name]['C_bet_count'] += 1
                    c_bet_made = True  # Mark that a C-bet has been made in this hand

                players_in_hand.add(player_name)

        # Increment the hands played for the players involved
        if pre_flop_raiser:
            player_stats[pre_flop_raiser]['hands_played'] += 1

    # Calculating final C-bet percentage
    for player_name, stats in player_stats.items():
        if stats['pre_flop_raise_count'] > 0:  # Avoid division by zero
            stats['C_bet'] = round(stats['C_bet_count'] / stats['pre_flop_raise_count'] * 100, 2)
        else:
            stats['C_bet'] = 0.0
        del stats['C_bet_count']  # Remove the count after calculating the percentage

    return player_stats
def calculate_showdown_stats(data):
    player_stats = {}

    for hand in data['hands']:
        flop_seen = False
        players_in_hand = set()  # Players who've played in this hand
        players_folded = set()  # Players who've folded in this hand
        players_at_showdown = set()  # Players who've reached showdown in this hand

        # Create a mapping of seat numbers to player names for this hand
        seat_to_name = {player['seat']: player['name'].lower() for player in hand['players']}

        for event in hand['events']:
            payload = event['payload']
            action_type = payload['type']
            player_seat = payload.get('seat', None)

            # Mark the flop event
            if 'turn' in payload and payload['turn'] == 1:  # Flop
                flop_seen = True

            # Initialize player stats if player_seat exists
            if player_seat:
                player_name = seat_to_name[player_seat]

                if player_name not in player_stats:
                    player_stats[player_name] = {
                        'showdown_count': 0, 'showdown_wins': 0, 'hands_played': 0
                    }

                # Track players who've folded
                if action_type == 11:  # Fold
                    players_folded.add(player_name)

                # Track showdowns
                if action_type == 15 and flop_seen and len(players_in_hand - players_folded) > 1:
                    player_stats[player_name]['showdown_count'] += 1
                    players_at_showdown.add(player_name)

                # Track showdown wins
                if action_type == 12 and player_name == seat_to_name[player_seat]:  # Win
                    player_stats[player_name]['showdown_wins'] += 1

                players_in_hand.add(player_name)
            
            for player in players_in_hand:
                player_stats[player]['hands_played'] += 1

        # Increment the hands played for the players involved
        for player in players_in_hand:
            player_stats[player]['hands_played'] += 1

    # Calculating final showdown percentages
    for player_name, stats in player_stats.items():
        if stats['showdown_count'] > 0:  # Avoid division by zero
            stats['Showdown Wins'] = round(stats['showdown_wins'] / stats['showdown_count'] * 100, 2)
        else:
            stats['Showdown Wins'] = 0.0
        del stats['showdown_wins']  # Remove the count after calculating the percentage

    return player_stats


def calculate_overall_stats(csv_directory, json_directory, big_blind):
    # Get a list of all CSV and JSON files
    csv_files = [f for f in os.listdir(csv_directory) if f.endswith('.csv')]
    json_files = [f for f in os.listdir(json_directory) if f.endswith('.json')]

    # Initialize an empty DataFrame to store the overall stats
    overall_stats_df = pd.DataFrame()

    # Loop over all files
    for csv_file, json_file in zip(csv_files, json_files):
        csv_filepath = os.path.join(csv_directory, csv_file)
        json_filepath = os.path.join(json_directory, json_file)

        # Calculate the stats for this file
        stats_df = main(json_filepath, csv_filepath)

        # Add the stats to the overall stats DataFrame
        overall_stats_df = pd.concat([overall_stats_df, stats_df])

    # Calculate the overall stats
    overall_stats_df = overall_stats_df.groupby(overall_stats_df.index).sum()

    # Calculate the percentages and BB/100 Hands for the overall stats
    
    overall_stats_df['VPIP'] = round(overall_stats_df['VPIP'] / overall_stats_df['hands_played'] * 100, 2)
    overall_stats_df['PFR'] = round(overall_stats_df['PFR'] / overall_stats_df['hands_played'] * 100, 2)
    overall_stats_df['Agg'] = round(overall_stats_df['Agg'] / overall_stats_df['hands_played'] * 100, 2)
    overall_stats_df['3bet'] = round(overall_stats_df['3bet'] / overall_stats_df['hands_played'] * 100, 2)
    overall_stats_df['4bet'] = round(overall_stats_df['4bet'] / overall_stats_df['hands_played'] * 100, 2)
    overall_stats_df['Fold_to_3bet'] = round(overall_stats_df['Fold_to_3bet'] / overall_stats_df['hands_played'] * 100, 2)
    #overall_stats_df['C_bet'] = round(overall_stats_df['C_bet'] / overall_stats_df['pre_flop_raise_count'] * 100, 2)
    overall_stats_df['Fold_to_C_bet'] = round(overall_stats_df['Fold_to_C_bet'] / overall_stats_df['hands_played'] * 100, 2)
    overall_stats_df['BB/100 Hands'] = round((overall_stats_df['PnL'] / overall_stats_df['hands_played'] * 100 ) * big_blind, 2)

    # Export the DataFrame to a CSV file
    overall_stats_df.reset_index().to_csv('Poker Hands/CSV Output/overall_player_stats.csv', index=False)

    return overall_stats_df

def calculate_fold_to_three_bet(data):
    player_stats = {}

    for hand in data['hands']:
        flop_seen = False
        raise_count = 0
        pre_flop_raiser = None
        three_bet_occurred = False
        players_in_hand = set()  # Players who've played in this hand

        # Create a mapping of seat numbers to player names for this hand
        seat_to_name = {player['seat']: player['name'].lower() for player in hand['players']}

        for event in hand['events']:
            payload = event['payload']
            action_type = payload['type']
            player_seat = payload.get('seat', None)

            # Mark the flop event
            if 'turn' in payload and payload['turn'] == 1:  # Flop
                flop_seen = True

            # Initialize player stats if player_seat exists
            if player_seat:
                player_name = seat_to_name[player_seat]

                if player_name not in player_stats:
                    player_stats[player_name] = {
                        'fold_to_3bet_count': 0, 'raise_count': 0, 'hands_played': 0
                    }

                # Track the pre-flop raiser
                if not flop_seen and action_type == 8 and raise_count == 0:  # First raise before flop
                    pre_flop_raiser = player_name
                    player_stats[player_name]['raise_count'] += 1
                    raise_count += 1

                # Track 3-bet
                if not flop_seen and action_type == 8 and raise_count == 1 and player_name != pre_flop_raiser:  # Second raise (3-bet) before flop by a different player
                    three_bet_occurred = True
                    raise_count += 1

                # Track fold to 3-bet
                if not flop_seen and action_type == 11 and player_name == pre_flop_raiser and three_bet_occurred:  # Fold after 3-bet
                    player_stats[player_name]['fold_to_3bet_count'] += 1

                players_in_hand.add(player_name)

        # Increment the hands played for the players involved
        for player in players_in_hand:
            player_stats[player]['hands_played'] += 1

    # Calculating final fold to 3-bet percentage
    for player_name, stats in player_stats.items():
        if stats['raise_count'] > 0:  # Avoid division by zero
            stats['Fold_to_3bet'] = round(stats['fold_to_3bet_count'] / stats['raise_count'] * 100, 2)
        else:
            stats['Fold_to_3bet'] = 0.0
        del stats['fold_to_3bet_count']  # Remove the count after calculating the percentage
        del stats['raise_count']  # Remove the count after calculating the percentage

    return player_stats


def calculate_fold_to_c_bet(data):
    player_stats = {}

    for hand in data['hands']:
        flop_seen = False
        pre_flop_raiser = None
        c_bet_made = False
        players_in_hand = set()  # Players who've played in this hand

        # Create a mapping of seat numbers to player names for this hand
        seat_to_name = {player['seat']: player['name'].lower() for player in hand['players']}

        for event in hand['events']:
            payload = event['payload']
            action_type = payload['type']
            player_seat = payload.get('seat', None)

            # Mark the flop event
            if 'turn' in payload and payload['turn'] == 1:  # Flop
                flop_seen = True

            # Initialize player stats if player_seat exists
            if player_seat:
                player_name = seat_to_name[player_seat]

                if player_name not in player_stats:
                    player_stats[player_name] = {
                        'fold_to_c_bet_count': 0, 'called_preflop_raise_count': 0, 'hands_played': 0
                    }

                # Track the pre-flop raiser
                if not flop_seen and action_type == 8:  # Raise before flop
                    pre_flop_raiser = player_name

                # Track players who called the pre-flop raise
                if not flop_seen and action_type == 7:  # Call before flop
                    player_stats[player_name]['called_preflop_raise_count'] += 1

                # Track C-bet
                if flop_seen and action_type == 8 and player_name == pre_flop_raiser:  # Bet after flop by pre-flop raiser
                    c_bet_made = True

                # Track fold to C-bet
                if flop_seen and action_type == 11 and c_bet_made:  # Fold after C-bet
                    player_stats[player_name]['fold_to_c_bet_count'] += 1

                players_in_hand.add(player_name)

        # Increment the hands played for the players involved
        for player in players_in_hand:
            player_stats[player]['hands_played'] += 1

    # Calculating final fold to C-bet percentage
    for player_name, stats in player_stats.items():
        if stats['called_preflop_raise_count'] > 0:  # Avoid division by zero
            stats['Fold_to_C_bet'] = round(stats['fold_to_c_bet_count'] / stats['called_preflop_raise_count'] * 100, 2)
        else:
            stats['Fold_to_C_bet'] = 0.0
        del stats['fold_to_c_bet_count']  # Remove the count after calculating the percentage
        del stats['called_preflop_raise_count']  # Remove the count after calculating the percentage

    return player_stats

def merge_players_stats(df, player1, player2):
    # Check if both players exist in the DataFrame
    if player1 in df.index and player2 in df.index:
        # Identify the columns to be summed and averaged
        sum_columns = ['hands_played', 'PnL', 'BB/100 Hands']
        avg_columns = [col for col in df.columns if col not in sum_columns]

        # Sum up the non-percentage statistics of the two players
        df.loc[player1, sum_columns] = df.loc[[player1, player2], sum_columns].sum()

        # Average the percentage statistics of the two players
        df.loc[player1, avg_columns] = df.loc[[player1, player2], avg_columns].mean()

        # Drop the row of the second player
        df = df.drop(player2)

    # Round all columns to 2 decimal places
    df = df.round(2)

    # Export the DataFrame to a CSV file
    df.to_csv('Poker Hands/CSV Output/merged_player_stats.csv')

    return df


def calculate_three_bet(data):
    player_stats = {}

    for hand in data['hands']:
        flop_seen = False
        raise_count = 0
        players_in_hand = set()  # Players who've played in this hand

        # Create a mapping of seat numbers to player names for this hand
        seat_to_name = {player['seat']: player['name'].lower() for player in hand['players']}

        for event in hand['events']:
            payload = event['payload']
            action_type = payload['type']
            player_seat = payload.get('seat', None)

            # Mark the flop event
            if 'turn' in payload and payload['turn'] == 1:  # Flop
                flop_seen = True

            # Initialize player stats if player_seat exists
            if player_seat:
                player_name = seat_to_name[player_seat]

                if player_name not in player_stats:
                    player_stats[player_name] = {
                        '3bet_count': 0, 'hands_played': 0
                    }

                # Track 3-bet
                if not flop_seen and action_type == 8:  # Raise before flop
                    raise_count += 1

                if raise_count == 2:  # Second raise is a 3-bet
                    player_stats[player_name]['3bet_count'] += 1
                    raise_count = 0  # Reset raise count for next hand

                players_in_hand.add(player_name)

        # Increment the hands played for the players involved
        for player in players_in_hand:
            player_stats[player]['hands_played'] += 1

    # Calculating final 3-bet percentage
    for player_name, stats in player_stats.items():
        stats['3bet'] = round(stats['3bet_count'] / stats['hands_played'] * 100, 2)
        del stats['3bet_count']  # Remove the count after calculating the percentage

    return player_stats


def calculate_four_bet(data):
    player_stats = {}

    for hand in data['hands']:
        flop_seen = False
        raise_count = 0
        players_in_hand = set()  # Players who've played in this hand

        # Create a mapping of seat numbers to player names for this hand
        seat_to_name = {player['seat']: player['name'].lower() for player in hand['players']}

        for event in hand['events']:
            payload = event['payload']
            action_type = payload['type']
            player_seat = payload.get('seat', None)

            # Mark the flop event
            if 'turn' in payload and payload['turn'] == 1:  # Flop
                flop_seen = True

            # Initialize player stats if player_seat exists
            if player_seat:
                player_name = seat_to_name[player_seat]

                if player_name not in player_stats:
                    player_stats[player_name] = {
                        '4bet_count': 0, 'hands_played': 0
                    }

                # Track 4-bet
                if not flop_seen and action_type == 8:  # Raise before flop
                    raise_count += 1

                if raise_count == 3:  # Third raise is a 4-bet
                    player_stats[player_name]['4bet_count'] += 1
                    raise_count = 0  # Reset raise count for next hand

                players_in_hand.add(player_name)

        # Increment the hands played for the players involved
        for player in players_in_hand:
            player_stats[player]['hands_played'] += 1

    # Calculating final 4-bet percentage
    for player_name, stats in player_stats.items():
        stats['4bet'] = round(stats['4bet_count'] / stats['hands_played'] * 100, 2)
        del stats['4bet_count']  # Remove the count after calculating the percentage

    return player_stats


def main(json_filepath, csv_filepath):
    with open(json_filepath, 'r') as file:
        data = json.load(file)
        vpip_stats = calculate_vpip(data)
        pfr_stats = calculate_pfr(data)
        agg_stats = calculate_agg(data)
        pnl_stats = calculate_pnl(csv_filepath)
        hands_played_stats = {player_name: stats['hands_played'] for player_name, stats in vpip_stats.items()}
        bb_per_100_hands_stats = calculate_bb_per_100_hands(pnl_stats, hands_played_stats, 0.5)
        three_bet_stats = calculate_three_bet(data)
        four_bet_stats = calculate_four_bet(data) 
        #c_bet_stats = calculate_c_bet(data)
        fold_to_3_bet_stats = calculate_fold_to_three_bet(data)
        fold_to_c_bet_stats = calculate_fold_to_c_bet(data)
        #showdown_stats = calculate_showdown_stats(data)

        # Convert each stats dictionary to a DataFrame
        vpip_df = pd.DataFrame.from_dict(vpip_stats, orient='index')
        pfr_df = pd.DataFrame.from_dict(pfr_stats, orient='index').drop(columns=['hands_played'])
        agg_df = pd.DataFrame.from_dict(agg_stats, orient='index').drop(columns=['hands_played'])
        pnl_df = pd.DataFrame.from_dict(pnl_stats, orient='index').rename(columns={0: 'PnL'})
        three_bet_df = pd.DataFrame.from_dict(three_bet_stats, orient='index').drop(columns=['hands_played'])
        four_bet_df = pd.DataFrame.from_dict(four_bet_stats, orient='index').drop(columns=['hands_played'])
        #c_bet_df = pd.DataFrame.from_dict(c_bet_stats, orient='index').drop(columns=['hands_played'])
        fold_to_3_bet_df = pd.DataFrame.from_dict(fold_to_3_bet_stats, orient='index').drop(columns=['hands_played'])
        fold_to_c_bet_df = pd.DataFrame.from_dict(fold_to_c_bet_stats, orient='index').drop(columns=['hands_played'])
        #showdown_df = pd.DataFrame.from_dict(showdown_stats, orient='index').drop(columns=['hands_played'])  # Add this line

        bb_per_100_hands_df = pd.DataFrame.from_dict(bb_per_100_hands_stats, orient='index').rename(columns={0: 'BB/100 Hands'})

        # Merge the DataFrames on the index (player name)
        df = pd.concat([vpip_df, pfr_df, agg_df, three_bet_df, four_bet_df, fold_to_3_bet_df, fold_to_c_bet_df, pnl_df, bb_per_100_hands_df], axis=1)  # Add showdown_df here

        return df

if __name__ == '__main__':
    csv_directory = 'Poker Hands/CSV Data'  # Replace with the path to your CSV files directory
    json_directory = 'Poker Hands/JSON Data'  # Replace with the path to your JSON files directory
    overall_stats_df = calculate_overall_stats(csv_directory, json_directory, 0.5)
    overall_stats_df = merge_players_stats(overall_stats_df, 'levels', 'norm')  # Replace 'player1' and 'player2' with the names of the players to merge
    print(overall_stats_df)