import json
import requests
from fractions import Fraction


# Fetch Elo from Chess.com given username
def fetch_chess_com_elo(chess_com_id):
    #print("began fetching elo")
    url = f"https://api.chess.com/pub/player/{chess_com_id}/stats"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        elo = data.get("chess_rapid", {}).get("last", {}).get("rating", None)
        #print(f"Elo Fetched: {elo}")
        return elo
    return None

# Fetch game data from Chess.com and update JSON file
def fetch_chess_com_games(player_name, json_file):
    # Load the existing data from the JSON file
    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print("Error: JSON file not found!")
        return
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from file!")
        return

    player_data = data.get(player_name, {})
    chess_com_id = player_data.get("chess_com_id")

    if not chess_com_id:
        print(f"Player {player_name} does not have a chess_com_id.")
        return

    # Get the archive URLs from Chess.com
    url = f"https://api.chess.com/pub/player/{chess_com_id}/games/archives"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    #print(f"Fetching archives for {player_name} from {url}...")  # Debug print
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch archives for {player_name}: Status Code {response.status_code}")
        if response.status_code == 404:
            print(f"Error 404: The player {player_name} does not exist on Chess.com.")
        elif response.status_code == 500:
            print("Error 500: Internal server error from Chess.com.")
        else:
            print(f"Unexpected response code: {response.status_code}")
        return

    # Get list of archive URLs (months)
    archives = response.json().get("archives", [])

    if not archives:
        print(f"No archives found for {player_name}")
        return

    #print(f"Found {len(archives)} archives for {player_name}.")  # Debug print

    existing_games = player_data.get("games", {})

    # Fetch each archive and its games
    for archive in archives:
        #print(f"Fetching games for archive: {archive}")  # Debug print

        games_response = requests.get(archive, headers=headers)

        if games_response.status_code != 200:
            print(f"Failed to fetch games from archive: {archive} - Status Code {games_response.status_code}")
            continue

        # Parse the games from the response
        games = games_response.json().get("games", [])
        #print(f"Found {len(games)} games in archive: {archive}")  # Debug print

        if not games:
            print(f"No games found in the archive {archive}. Skipping...")
            continue

        for game in games:
            timestamp = str(game.get("end_time"))

            # Skip game if it's already in the JSON data
            if timestamp in existing_games:
                #print(f"Skipping existing game with timestamp: {timestamp}")
                continue

            #print(f"Adding new game with timestamp: {timestamp}")  # Debug print

            # Determine if the player is white or black
            is_white = game["white"]["username"].lower() == chess_com_id.lower()
            opponent = game["black"] if is_white else game["white"]

            # Create the game data
            game_data = {
                "white": is_white,
                "OpponentElo": opponent.get("rating", 0),
                "EloBeforeGame": game["white"].get("rating", 0) if is_white else game["black"].get("rating", 0),
                "EloAfterGame": game["white"].get("rating_post", 0) if is_white else game["black"].get("rating_post", 0),
                "Result": "win" if game["white"].get("result") == "win" and is_white else "loss" if game["black"].get("result") == "win" and not is_white else "draw",
                "TimeLeft(seconds)": game.get("time_control", "0")
            }

            # Add this game to the player's existing games
            existing_games[timestamp] = game_data

        # Update the player's data with the new games
        player_data["games"] = existing_games
        data[player_name] = player_data

        # Save the updated data back to the JSON file
        try:
            with open(json_file, 'w') as file:
                json.dump(data, file, indent=4)
            print(f"Successfully updated games for {player_name}.")  # Debug print
        except IOError:
            print(f"Error: Unable to save the updated data to {json_file}.")
            return

    #print(f"JSON file updated for {player_name}")

# Update Elo from Chess.com
def update_elo_from_chess_com(json_file):
    #print("Updating Elo from Chess.com")
    with open(json_file, 'r') as file:
        data = json.load(file)

    for player, details in data.items():
        if "chess_com_id" in details:
            new_elo = fetch_chess_com_elo(details["chess_com_id"])
            #print(f"Located {player}'s username: {details["chess_com_id"]}")
            data[player]["elo"] = new_elo
            #print(f"{new_elo} Is {player}'s Refreshed ELO ")
        else:
            print("Unable to locate Player Username")

    with open(json_file, 'w') as file:
        json.dump(data, file, indent=4)

def calculate_total_wins(json_file, playername):
    with open(json_file, 'r') as file:
        data = json.load(file)
    player_data = data.get(playername, {})
    chess_com_id = player_data.get("chess_com_id")

    if not chess_com_id:
        print(f"Player {playername} does not have a chess_com_id.")
        return

    url = f"https://api.chess.com/pub/player/{chess_com_id}/stats"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    #print(f"Fetching Win Statisitcs for {playerName} from {url}...")  # Debug print
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch archives for {playername}: Status Code {response.status_code}")
        if response.status_code == 404:
            print(f"Error 404: The player {playername} does not exist on Chess.com.")
        elif response.status_code == 500:
            print("Error 500: Internal server error from Chess.com.")
        else:
            print(f"Unexpected response code: {response.status_code}")
        return

    #print(f"Response Code: {response.status_code}")

    wins = response.json().get("chess_rapid", {}).get("record", {}).get("win", None)
    #print(f"Wins fetched from {chess_com_id}: {wins}")
    data[playername]["wins"] = wins
    stalemates = response.json().get("chess_rapid", {}).get("record", {}).get("draw", None)
    #print(f"Draws fetched from {chess_com_id}: {stalemates}")
    data[playername]["stalemates"] = stalemates
    losses = response.json().get("chess_rapid", {}).get("record", {}).get("loss", None)
    #print(f"Losses fetched from {chess_com_id}: {losses}")
    data[playername]["losses"] = losses

    try:
        with open(json_file, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"Successfully updated Win Stats for {playername}.")  # Debug print
    except IOError:
        print(f"Error: Unable to save the updated data to {json_file}.")
        return


# Calculate odds from the JSON file based on the two selected players
def calculate_odds_from_json(json_file, player1_name, player2_name, is_white1):
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Extract player data
    player1 = data.get(player1_name)
    player2 = data.get(player2_name)

    if not player1 or not player2:
        raise ValueError("One or both player names not found in JSON file.")

    elo1, wins1, draws1, losses1 = player1["elo"], player1["wins"], player1["stalemates"], player1["losses"]
    elo2, wins2, draws2, losses2 = player2["elo"], player2["wins"], player2["stalemates"], player2["losses"]

    # Base probability using Elo formula
    def expected_score(elo_a, elo_b):
        return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

    prob1 = expected_score(elo1, elo2)

    # Adjust for win/loss/draw history (basic weighting)
    total_games1 = max(wins1 + draws1 + losses1, 1)
    total_games2 = max(wins2 + draws2 + losses2, 1)
    win_rate1 = wins1 / total_games1
    win_rate2 = wins2 / total_games2
    draw_rate1 = draws1 / total_games1
    draw_rate2 = draws2 / total_games2

    avg_win_rate = (win_rate1 + (1 - win_rate2)) / 2
    avg_draw_rate = (draw_rate1 + draw_rate2) / 2

    prob1 = (prob1 * 0.7) + (avg_win_rate * 0.2) + (avg_draw_rate * 0.1)
    prob2 = 1 - prob1

    # Adjust for White advantage (~54% chance to not lose)
    if is_white1:
        prob1 *= 1.05
        prob2 *= 0.95
    else:
        prob1 *= 0.95
        prob2 *= 1.05

    # Normalize probabilities
    total_prob = prob1 + prob2
    prob1 /= total_prob
    prob2 /= total_prob

    # Convert to decimal odds (without profit margin)
    odds1 = 1 / prob1
    odds2 = 1 / prob2

    # Apply 8% profit margin
    margin = 1.15
    odds1 /= margin
    odds2 /= margin

    # Convert to fractional odds (limit denominator to a max of 15)
    def limit_fraction(odds):
        fraction = Fraction(odds - 1).limit_denominator(15)
        return f"{fraction.numerator}/{fraction.denominator}"

    frac_odds1 = limit_fraction(odds1)
    frac_odds2 = limit_fraction(odds2)

    # Implied probabilities
    implied_prob1 = (1 / odds1) * 100
    implied_prob2 = (1 / odds2) * 100

    # Raw probabilities before margin
    raw_prob1 = prob1 * 115
    raw_prob2 = prob2 * 115

    return {
        player1_name: {
            "Decimal Odds": round(odds1, 2),
            "Fractional Odds": frac_odds1,
            "Implied Probability": round(implied_prob1, 2),
            "Raw Probability": round(raw_prob1, 2),
        },
        player2_name: {
            "Decimal Odds": round(odds2, 2),
            "Fractional Odds": frac_odds2,
            "Implied Probability": round(implied_prob2, 2),
            "Raw Probability": round(raw_prob2, 2),
        }
    }


def load_betting_data():
    try:
        with open("Data/bets.json", "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_betting_data(data):
    with open("Data/bets.json", "w") as file:
        json.dump(data, file, indent=4)


def place_bets(odds, player1_name, player2_name):
    betting_data = load_betting_data()

    while True:
        bettor_name = input("Enter your name: ")
        chosen_player = input(f"Which player are you betting on ({player1_name}, {player2_name}, or 'draw')? ").strip()
        bet_amount = float(input("Enter your bet amount: "))

        if chosen_player not in [player1_name, player2_name, 'draw']:
            print("Invalid player. Please choose a valid option.")
            continue

        bet_odds = odds.get(chosen_player, {})
        if not bet_odds:
            print("Invalid bet selection.")
            continue

        decimal_odds = bet_odds["Decimal Odds"]
        fractional_odds = bet_odds["Fractional Odds"]
        potential_payout = round(bet_amount * decimal_odds, 2)

        confirm = input(
            f"Confirm bet: {bettor_name} bets ${bet_amount} on {chosen_player} with odds {fractional_odds} (yes/no): "
        ).strip().lower()

        if confirm != "yes":
            print("Bet canceled.")
            continue

        bet_entry = {
            "player": chosen_player,
            "bet_type": "win",
            "amount": bet_amount,
            "odds": fractional_odds,
            "potential_payout": potential_payout,
            "result": "pending",
            "actual_payout": 0
        }

        if bettor_name not in betting_data:
            betting_data[bettor_name] = {"bets": [], "total_payout": 0}

        betting_data[bettor_name]["bets"].append(bet_entry)
        save_betting_data(betting_data)

        print("Bet placed successfully!")

        more_bets = input("Would you like to place another bet? (yes/no): ").strip().lower()
        if more_bets != "yes":
            break


def process_bets(winning_player):
    betting_data = load_betting_data()
    print(f"Processing bets... The winner is {winning_player}.")

    for bettor, data in betting_data.items():
        total_payout = 0
        for bet in data["bets"]:
            if bet["player"] == winning_player:
                bet["result"] = "win"
                bet["actual_payout"] = bet["potential_payout"]
                total_payout += bet["actual_payout"]
                print(f"{bettor} wins ${bet['actual_payout']}")
            else:
                bet["result"] = "loss"
                bet["actual_payout"] = 0
                print(f"{bettor} loses ${bet['amount']}")

        data["total_payout"] = total_payout

    save_betting_data(betting_data)
    print("Betting results saved.")

def add_new_player(json_file):
    # Ask for new player's name and Chess.com username
    new_player_name = input("Enter the new player's name: ").strip()
    new_chess_com_id = input(f"Enter {new_player_name}'s username on Chess.com: ").strip()

    # Load the existing data from the JSON file
    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {}  # If file doesn't exist, start with an empty dictionary
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from file!")
        return

    # Check if the player already exists
    if new_player_name in data:
        print(f"Player {new_player_name} already exists in the database.")
        return

    # Add new player data
    data[new_player_name] = {
        "chess_com_id": new_chess_com_id,
        "elo": 0,
        "wins": 0,
        "stalemates": 0,
        "losses": 0,
        "games": {}
    }

    # Save the updated data back to the JSON file
    try:
        with open(json_file, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"New player {new_player_name} added successfully!")
    except IOError:
        print(f"Error: Unable to save the updated data to {json_file}.")
        return

# Main interactive function to ask for player names and calculate odds
def main():
    json_file = "Data/Players.json"

    # Ask for player names
    player1_name = input("Enter the first player's name: ")
    if player1_name.lower() == "new":
        add_new_player(json_file)
        player1_name = input("Enter the first player's name again: ")
    player2_name = input("Enter the second player's name: ")
    if player2_name.lower() == "new":
        add_new_player(json_file)
        player2_name = input("Enter the second player's name again: ")
    is_white1 = input(f"Is {player1_name} playing as white? (yes/no): ").lower() == "yes"

    # Fetch and update player data
    update_elo_from_chess_com(json_file)
    fetch_chess_com_games(player1_name, json_file)
    fetch_chess_com_games(player2_name, json_file)
    calculate_total_wins(json_file, player1_name)
    calculate_total_wins(json_file, player2_name)

    # Calculate odds
    odds = calculate_odds_from_json(json_file, player1_name, player2_name, is_white1)

    # Print the odds
    for player, stats in odds.items():
        print(f"\n{player}:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    place_bets(odds, player1_name, player2_name)

    winner = input("Enter the winner of the match (or 'draw'): ").strip()
    process_bets(winner)

# Run the interactive function
if __name__ == "__main__":
    main()
