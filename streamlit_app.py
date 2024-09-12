import streamlit as st
import re
import pandas as pd
import altair as alt

def safe_split(s, delimiter, max_split=1):
    parts = s.split(delimiter, max_split)
    return parts[-1] if len(parts) > 1 else s

def parse_log_file(log_content):
    games = []
    current_game = {'game_number': 1, 'starting_hands': {}, 'points': {}, 'rounds': [], 'card_counts': [], 'team_horizon_hands': []}
    player_names = set()
    current_card_count = {}
    team_horizon_hand = []
    to_beat = None

    for line in log_content.split('\n'):
        if 'Starting Game' in line:
            if current_game['rounds']:
                games.append(current_game)
            game_number = int(re.search(r'Starting Game (\d+)', line).group(1))
            current_game = {'game_number': game_number, 'starting_hands': {}, 'points': {}, 'rounds': [], 'card_counts': [], 'team_horizon_hands': []}
            current_card_count = {}
            team_horizon_hand = []
            to_beat = None
        
        elif 'You were dealt' in line:
            player = safe_split(line.split(':')[0], ": ")
            cards = re.findall(r"'([^']*)'", line)
            current_game['starting_hands'][player] = cards
            current_card_count[player] = len(cards)
            player_names.add(player)
            if player == 'Team Horizon':
                team_horizon_hand = cards
        
        elif 'To beat:' in line:
            to_beat = re.findall(r"'([^']*)'", line)
            to_beat = to_beat[0] if to_beat else 'None'
        
        elif 'finished with' in line:
            parts = line.split()
            try:
                finished_index = parts.index('finished')
                player = ' '.join(parts[:finished_index])
                player = safe_split(player, ": ")
                points = int(parts[-2])
                current_game['points'][player] = points
                player_names.add(player)
            except (ValueError, IndexError):
                continue
        
        elif 'played' in line:
            try:
                parts = line.split()
                played_index = parts.index('played')
                player = ' '.join(parts[:played_index])
                player = safe_split(player, ": ")
                cards = re.findall(r"'([^']*)'", line)
                if cards and player in current_card_count:
                    current_game['rounds'].append({'player': player, 'cards': cards, 'to_beat': to_beat})
                    current_card_count[player] = max(0, current_card_count[player] - len(cards))
                    current_game['card_counts'].append(current_card_count.copy())
                    if player == 'Team Horizon':
                        for card in cards:
                            if card in team_horizon_hand:
                                team_horizon_hand.remove(card)
                    current_game['team_horizon_hands'].append(team_horizon_hand.copy())
                    to_beat = cards[-1] if cards else None  # Update to_beat for the next play
                player_names.add(player)
            except (ValueError, IndexError):
                continue

        elif 'won the game' in line or 'won the round' in line:
            player = safe_split(line.split()[0], ": ")
            if player in current_card_count:
                current_card_count[player] = 0
                current_game['card_counts'].append(current_card_count.copy())
                if player == 'Team Horizon':
                    team_horizon_hand = []
                current_game['team_horizon_hands'].append(team_horizon_hand.copy())
            player_names.add(player)
            to_beat = None  # Reset to_beat after a win

    if current_game['rounds']:
        games.append(current_game)

    return games, list(player_names)

def create_points_dataframe(games, player_names):
    data = []
    for game in games:
        game_data = {'Game': game['game_number']}
        for player in player_names:
            game_data[player] = game['points'].get(player, 0)
        data.append(game_data)
    return pd.DataFrame(data)

def create_card_count_dataframe(game):
    data = []
    for round_num, card_count in enumerate(game['card_counts'], 1):
        round_data = {'Round': round_num}
        round_data.update(card_count)
        data.append(round_data)
    return pd.DataFrame(data)

def create_game_events(game):
    events = []
    for round_num, (round_data, card_count, team_horizon_hand) in enumerate(zip(game['rounds'], game['card_counts'], game['team_horizon_hands']), 1):
        events.append({
            'event_type': 'play',
            'round': round_num,
            'player': round_data['player'],
            'to_beat': round_data['to_beat'],
            'cards_played': ', '.join(round_data['cards']),
            'card_counts': card_count,
            'team_horizon_hand': ', '.join(team_horizon_hand)
        })
    
    # Add game end event
    events.append({
        'event_type': 'game_end',
        'round': round_num + 1,
        'player': max(game['points'], key=game['points'].get),
        'to_beat': 'N/A',
        'cards_played': 'Game End',
        'card_counts': game['points'],
        'team_horizon_hand': ''
    })
    
    return events

def main():
    st.title("Big 2 Game Analysis Dashboard")

    uploaded_file = st.file_uploader("Choose a log file", type="txt")
    if uploaded_file is not None:
        log_content = uploaded_file.getvalue().decode("utf-8")
        games, player_names = parse_log_file(log_content)

        if not games:
            st.error("No game data could be parsed from the log file. Please check the file format.")
            return

        st.header("Points Progression")
        points_df = create_points_dataframe(games, player_names)
        st.line_chart(points_df.set_index('Game'))

        st.header("Game Review")
        selected_game = st.selectbox("Select a game to review", range(1, len(games) + 1))
        game = games[selected_game - 1]
        
        events = create_game_events(game)
        
        event_index = st.slider("Event", 0, len(events) - 1, 0)
        event = events[event_index]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"Round {event['round']}")
            st.write(f"Player: {event['player']}")
            st.write(f"To Beat: {event['to_beat']}")
            st.write(f"Played: {event['cards_played']}")
        
        with col2:
            st.subheader("Card Counts")
            for player, count in event['card_counts'].items():
                st.write(f"{player}: {count}")
        
        if 'Team Horizon' in event['card_counts']:
            st.subheader("Team Horizon's Hand")
            st.write(event['team_horizon_hand'])

        st.header("Cards Held Per Round")
        card_count_df = create_card_count_dataframe(game)
        
        # Melt the dataframe to create a format suitable for Altair
        melted_df = card_count_df.melt(id_vars=['Round'], var_name='Player', value_name='Cards')
        
        # Create the Altair chart
        chart = alt.Chart(melted_df).mark_line(point=True).encode(
            x='Round:Q',
            y='Cards:Q',
            color='Player:N',
            tooltip=['Round', 'Player', 'Cards']
        ).properties(
            width=600,
            height=400
        ).interactive()

        st.altair_chart(chart, use_container_width=True)

        st.header("Final Scores")
        final_scores = points_df.iloc[-1].sort_values(ascending=False)
        st.bar_chart(final_scores)

if __name__ == "__main__":
    main()
