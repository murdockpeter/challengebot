# ChallengeBot - Discord Board Game Challenge Bot

A Discord bot that allows players to challenge each other to board games, track results, and maintain leaderboards. Built with Python, Discord.py, and Firebase Firestore.

## Features

- 🎮 **Challenge System**: Challenge other players to board games
- ✅ **Accept/Decline**: Players can accept or decline challenges
- 📊 **Result Tracking**: Report wins, losses, and draws
- 🏆 **Leaderboards**: View leaderboards for each supported game
- 📈 **Statistics**: Track individual player statistics
- 🗂️ **Firebase Integration**: Store all data in Firebase Firestore for future Flutter app integration

## Supported Games

- Chess
- Checkers
- Monopoly
- Risk
- Scrabble
- Catan
- Ticket to Ride
- Pandemic
- Carcassonne
- Dominion

## Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `!challenge` | Challenge another player to a board game | `!challenge @player <game>` |
| `!accept` | Accept a pending challenge | `!accept <challenge_id>` |
| `!report` | Report the result of a completed game | `!report <challenge_id> <win/loss/draw> [winner_id]` |
| `!leaderboard` | Show leaderboard for a specific game | `!leaderboard <game>` |
| `!stats` | Show statistics for yourself or another player | `!stats [@player] [game]` |
| `!challenges` | Show your pending and active challenges | `!challenges` |
| `!cancel` | Cancel a pending challenge (challenger only) | `!cancel <challenge_id>` |
| `!games` | Show all supported games | `!games` |
| `!help` | Show help information | `!help` |

## Setup Instructions

### 1. Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Firebase Project with Firestore enabled

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section and create a bot
4. Copy the bot token
5. Enable the following bot permissions:
   - Send Messages
   - Embed Links
   - Read Message History
   - Use Slash Commands
6. Invite the bot to your server

### 4. Firebase Setup

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select an existing one
3. Enable Firestore Database
4. Go to Project Settings > Service Accounts
5. Generate a new private key (JSON file)
6. Copy the values from the JSON file to your environment variables

### 5. Environment Configuration

1. Copy `env_example.txt` to `.env`
2. Fill in your configuration values:

```env
# Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_GUILD_ID=your_guild_id_here

# Firebase Configuration
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_PRIVATE_KEY_ID=your_firebase_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour private key here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your_firebase_client_email
FIREBASE_CLIENT_ID=your_firebase_client_id
FIREBASE_CLIENT_X509_CERT_URL=your_firebase_client_x509_cert_url
```

### 6. Run the Bot

```bash
python bot.py
```

## Usage Examples

### Challenging a Player
```
!challenge @Alice Chess
```
This creates a challenge for Alice to play Chess.

### Accepting a Challenge
```
!accept abc123def456
```
This accepts the challenge with ID `abc123def456`.

### Reporting a Win
```
!report abc123def456 win
```
This reports that you won the game.

### Reporting a Loss
```
!report abc123def456 loss
```
This reports that you lost the game.

### Reporting a Draw
```
!report abc123def456 draw
```
This reports that the game ended in a draw.

### Viewing Leaderboard
```
!leaderboard Chess
```
This shows the top players for Chess.

### Viewing Your Stats
```
!stats
```
This shows your statistics across all games.

## Database Schema

### Challenges Collection
```json
{
  "challenger_id": 123456789,
  "challenger_name": "Player1",
  "opponent_id": 987654321,
  "opponent_name": "Player2",
  "game": "Chess",
  "status": "pending|accepted|completed|cancelled",
  "result": "win|loss|draw|null",
  "winner_id": 123456789,
  "loser_id": 987654321,
  "created_at": "2024-01-01T12:00:00Z",
  "accepted_at": "2024-01-01T12:05:00Z",
  "completed_at": "2024-01-01T13:00:00Z"
}
```

### Player Stats Collection
```json
{
  "player_id": 123456789,
  "game": "Chess",
  "wins": 5,
  "losses": 3,
  "draws": 1,
  "total_games": 9
}
```

## Future Enhancements

- [ ] Flutter mobile app integration
- [ ] Tournament system
- [ ] Game-specific statistics
- [ ] Challenge notifications
- [ ] Automated matchmaking
- [ ] Game history tracking
- [ ] Achievement system

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.
