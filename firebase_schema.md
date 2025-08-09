# Firebase Firestore Schema for ChallengeBot

## Database Structure

### Collections Overview

```
challengebot/
├── challenges/          # Game challenges
├── player_stats/        # Player statistics per game
├── users/              # User profiles (optional)
└── games/              # Game metadata (optional)
```

## 1. Challenges Collection

**Document ID**: Auto-generated
**Path**: `challenges/{challengeId}`

```json
{
  "challenger_id": 123456789,
  "challenger_name": "Player1",
  "opponent_id": 987654321,
  "opponent_name": "Player2",
  "game": "Chess",
  "status": "pending", // "pending", "accepted", "completed", "cancelled"
  "result": null, // "win", "loss", "draw", null
  "winner_id": null, // Discord user ID of winner
  "loser_id": null,  // Discord user ID of loser
  "created_at": "2024-01-01T12:00:00Z",
  "accepted_at": null, // Timestamp when accepted
  "completed_at": null, // Timestamp when completed
  "discord_guild_id": 123456789, // Discord server ID
  "discord_channel_id": 987654321 // Discord channel ID
}
```

**Indexes needed:**
- `opponent_id` (Ascending) + `status` (Ascending)
- `challenger_id` (Ascending) + `status` (Ascending)
- `status` (Ascending) + `created_at` (Descending)

## 2. Player Stats Collection

**Document ID**: `{playerId}_{gameName}`
**Path**: `player_stats/{playerId}_{gameName}`

```json
{
  "player_id": 123456789,
  "player_name": "Player1",
  "game": "Chess",
  "wins": 5,
  "losses": 3,
  "draws": 1,
  "total_games": 9,
  "win_rate": 55.6, // Calculated field
  "last_played": "2024-01-01T12:00:00Z",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**Indexes needed:**
- `game` (Ascending) + `wins` (Descending)
- `player_id` (Ascending) + `game` (Ascending)

## 3. Users Collection (Optional)

**Document ID**: `{playerId}`
**Path**: `users/{playerId}`

```json
{
  "player_id": 123456789,
  "player_name": "Player1",
  "discord_username": "player1#1234",
  "created_at": "2024-01-01T10:00:00Z",
  "last_seen": "2024-01-01T12:00:00Z",
  "preferences": {
    "favorite_games": ["Chess", "Catan"],
    "notifications_enabled": true
  },
  "total_challenges": 15,
  "total_games_played": 25
}
```

## 4. Games Collection (Optional)

**Document ID**: `{gameName}`
**Path**: `games/{gameName}`

```json
{
  "name": "Chess",
  "display_name": "Chess",
  "description": "Classic strategy board game",
  "min_players": 2,
  "max_players": 2,
  "is_active": true,
  "total_challenges": 150,
  "total_games_played": 120,
  "created_at": "2024-01-01T10:00:00Z"
}
```

## Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Challenges collection
    match /challenges/{challengeId} {
      allow read: if request.auth != null || 
                   resource.data.challenger_id == request.auth.uid ||
                   resource.data.opponent_id == request.auth.uid;
      allow write: if request.auth != null;
    }
    
    // Player stats collection
    match /player_stats/{docId} {
      allow read: if true; // Public read for leaderboards
      allow write: if request.auth != null;
    }
    
    // Users collection
    match /users/{userId} {
      allow read, write: if request.auth != null && 
                          request.auth.uid == userId;
    }
    
    // Games collection
    match /games/{gameName} {
      allow read: if true; // Public read
      allow write: if request.auth != null; // Admin only in production
    }
  }
}
```

## Setup Instructions

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project"
3. Enter project name: `challengebot` (or your preferred name)
4. Enable Google Analytics (optional)
5. Click "Create project"

### 2. Enable Firestore Database

1. In your Firebase project, go to "Firestore Database"
2. Click "Create database"
3. Choose "Start in test mode" (for development)
4. Select a location (choose closest to your users)
5. Click "Done"

### 3. Create Collections

The collections will be created automatically when your bot first writes data, but you can create them manually:

1. Go to Firestore Database
2. Click "Start collection"
3. Create collections: `challenges`, `player_stats`, `users`, `games`

### 4. Set Up Indexes

1. Go to Firestore Database → Indexes
2. Click "Create index"
3. Add the following composite indexes:

**For challenges collection:**
- Collection ID: `challenges`
- Fields: `opponent_id` (Ascending), `status` (Ascending)
- Fields: `challenger_id` (Ascending), `status` (Ascending)
- Fields: `status` (Ascending), `created_at` (Descending)

**For player_stats collection:**
- Collection ID: `player_stats`
- Fields: `game` (Ascending), `wins` (Descending)
- Fields: `player_id` (Ascending), `game` (Ascending)

### 5. Generate Service Account Key

1. Go to Project Settings (gear icon)
2. Click "Service accounts" tab
3. Click "Generate new private key"
4. Download the JSON file
5. Copy the values to your `.env` file

### 6. Update Security Rules (Optional)

1. Go to Firestore Database → Rules
2. Replace the default rules with the ones above
3. Click "Publish"

## Data Flow Examples

### Creating a Challenge
```python
# Bot creates challenge
challenge_data = {
    "challenger_id": 123456789,
    "challenger_name": "Alice",
    "opponent_id": 987654321,
    "opponent_name": "Bob",
    "game": "Chess",
    "status": "pending",
    # ... other fields
}
db.collection('challenges').add(challenge_data)
```

### Updating Player Stats
```python
# After game completion
stats_ref = db.collection('player_stats').document(f"{winner_id}_{game}")
stats_ref.update({
    "wins": firestore.Increment(1),
    "total_games": firestore.Increment(1),
    "updated_at": datetime.now()
})
```

### Querying Leaderboard
```python
# Get top players for Chess
leaderboard = db.collection('player_stats')\
    .where('game', '==', 'Chess')\
    .order_by('wins', direction=firestore.Query.DESCENDING)\
    .limit(10)\
    .stream()
```

## Future Flutter App Integration

The same schema will work perfectly with your Flutter app:

```dart
// Flutter example
final challenges = await FirebaseFirestore.instance
    .collection('challenges')
    .where('status', isEqualTo: 'accepted')
    .get();
```

This schema is designed to be:
- ✅ Scalable for large numbers of users
- ✅ Efficient for common queries
- ✅ Compatible with both Discord bot and Flutter app
- ✅ Easy to extend with new features
