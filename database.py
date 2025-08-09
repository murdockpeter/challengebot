import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import config

class ChallengeDatabase:
    def __init__(self):
        """Initialize Firebase connection and Firestore client"""
        try:
            # Initialize Firebase with service account
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": config.FIREBASE_PROJECT_ID,
                "private_key_id": config.FIREBASE_PRIVATE_KEY_ID,
                "private_key": config.FIREBASE_PRIVATE_KEY,
                "client_email": config.FIREBASE_CLIENT_EMAIL,
                "client_id": config.FIREBASE_CLIENT_ID,
                "auth_uri": config.FIREBASE_AUTH_URI,
                "token_uri": config.FIREBASE_TOKEN_URI,
                "auth_provider_x509_cert_url": config.FIREBASE_AUTH_PROVIDER_X509_CERT_URL,
                "client_x509_cert_url": config.FIREBASE_CLIENT_X509_CERT_URL
            })
            
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            print("Firebase connection established successfully!")
            
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            raise

    def create_challenge(self, challenger_id: int, challenger_name: str, 
                        opponent_id: int, opponent_name: str, game: str) -> str:
        """Create a new challenge in the database"""
        try:
            challenge_data = {
                "challenger_id": challenger_id,
                "challenger_name": challenger_name,
                "opponent_id": opponent_id,
                "opponent_name": opponent_name,
                "game": game,
                "status": "pending",  # pending, accepted, completed, cancelled
                "result": None,  # win, loss, draw
                "winner_id": None,
                "loser_id": None,
                "created_at": datetime.now(),
                "accepted_at": None,
                "completed_at": None
            }
            
            doc_ref = self.db.collection('challenges').add(challenge_data)
            return doc_ref[1].id
            
        except Exception as e:
            print(f"Error creating challenge: {e}")
            raise

    def get_pending_challenges_for_user(self, user_id: int) -> List[Dict]:
        """Get all pending challenges for a specific user (both as challenger and opponent)"""
        try:
            # Get challenges where user is the opponent
            opponent_challenges = self.db.collection('challenges').where(
                filter=firestore.FieldFilter('opponent_id', '==', user_id)
            ).where(
                filter=firestore.FieldFilter('status', '==', 'pending')
            ).stream()
            
            # Get challenges where user is the challenger
            challenger_challenges = self.db.collection('challenges').where(
                filter=firestore.FieldFilter('challenger_id', '==', user_id)
            ).where(
                filter=firestore.FieldFilter('status', '==', 'pending')
            ).stream()
            
            all_challenges = []
            
            for doc in opponent_challenges:
                all_challenges.append({"id": doc.id, **doc.to_dict()})
                
            for doc in challenger_challenges:
                all_challenges.append({"id": doc.id, **doc.to_dict()})
                
            return all_challenges
            
        except Exception as e:
            print(f"Error getting pending challenges: {e}")
            return []

    def accept_challenge(self, challenge_id: str, accepted_by_id: int) -> bool:
        """Accept a challenge"""
        try:
            challenge_ref = self.db.collection('challenges').document(challenge_id)
            challenge = challenge_ref.get()
            
            if not challenge.exists:
                return False
                
            challenge_data = challenge.to_dict()
            if challenge_data['opponent_id'] != accepted_by_id:
                return False
                
            challenge_ref.update({
                'status': 'accepted',
                'accepted_at': datetime.now()
            })
            return True
            
        except Exception as e:
            print(f"Error accepting challenge: {e}")
            return False

    def report_result(self, challenge_id: str, reporter_id: int, 
                     result: str, winner_id: int = None, loser_id: int = None) -> bool:
        """Report the result of a completed game"""
        try:
            challenge_ref = self.db.collection('challenges').document(challenge_id)
            challenge = challenge_ref.get()
            
            if not challenge.exists:
                return False
                
            challenge_data = challenge.to_dict()
            if challenge_data['status'] != 'accepted':
                return False
                
            if reporter_id not in [challenge_data['challenger_id'], challenge_data['opponent_id']]:
                return False
                
            # Update challenge with result
            update_data = {
                'status': 'completed',
                'result': result,
                'completed_at': datetime.now()
            }
            
            if result in ['win', 'loss']:
                update_data['winner_id'] = winner_id
                update_data['loser_id'] = loser_id
                
            challenge_ref.update(update_data)
            
            # Update player statistics
            self._update_player_stats(
                challenge_data['game'], 
                challenge_data['challenger_id'], 
                challenge_data['challenger_name'],
                challenge_data['opponent_id'],
                challenge_data['opponent_name'],
                winner_id, 
                loser_id, 
                result
            )
            
            return True
            
        except Exception as e:
            print(f"Error reporting result: {e}")
            return False

    def _update_player_stats(self, game: str, challenger_id: int, challenger_name: str,
                           opponent_id: int, opponent_name: str, winner_id: int, loser_id: int, result: str):
        """Update player statistics for a game"""
        try:
            if result == 'draw':
                # Handle draw - both players get a draw recorded
                self._update_single_player_stats(challenger_id, challenger_name, game, 0, 0, 1)
                self._update_single_player_stats(opponent_id, opponent_name, game, 0, 0, 1)
                return
            
            # Update winner stats
            if winner_id:
                winner_name = challenger_name if winner_id == challenger_id else opponent_name
                self._update_single_player_stats(winner_id, winner_name, game, 1, 0, 0)
            
            # Update loser stats
            if loser_id:
                loser_name = challenger_name if loser_id == challenger_id else opponent_name
                self._update_single_player_stats(loser_id, loser_name, game, 0, 1, 0)
                    
        except Exception as e:
            print(f"Error updating player stats: {e}")

    def _update_single_player_stats(self, player_id: int, player_name: str, game: str, wins: int, losses: int, draws: int):
        """Update stats for a single player"""
        try:
            stats_ref = self.db.collection('player_stats').document(f"{player_id}_{game}")
            stats = stats_ref.get()
            
            if stats.exists:
                data = stats.to_dict()
                data['wins'] = data.get('wins', 0) + wins
                data['losses'] = data.get('losses', 0) + losses
                data['draws'] = data.get('draws', 0) + draws
                data['total_games'] = data.get('total_games', 0) + 1
                data['player_name'] = player_name  # Update name in case it changed
                stats_ref.update(data)
            else:
                stats_ref.set({
                    'player_id': player_id,
                    'player_name': player_name,
                    'game': game,
                    'wins': wins,
                    'losses': losses,
                    'draws': draws,
                    'total_games': 1
                })
                
        except Exception as e:
            print(f"Error updating single player stats: {e}")

    def get_leaderboard(self, game: str, limit: int = 10) -> List[Dict]:
        """Get leaderboard for a specific game"""
        try:
            stats = self.db.collection('player_stats').where(
                'game', '==', game
            ).order_by('wins', direction=firestore.Query.DESCENDING).limit(limit).stream()
            
            leaderboard = []
            for doc in stats:
                data = doc.to_dict()
                win_rate = (data['wins'] / data['total_games']) * 100 if data['total_games'] > 0 else 0
                leaderboard.append({
                    **data,
                    'win_rate': round(win_rate, 1)
                })
                
            return leaderboard
            
        except Exception as e:
            print(f"Error getting leaderboard: {e}")
            return []

    def get_overall_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get overall leaderboard aggregated across all games with breakdown"""
        try:
            # Get all player stats
            all_stats = self.db.collection('player_stats').stream()
            
            # Aggregate stats by player
            player_totals = {}
            for doc in all_stats:
                data = doc.to_dict()
                player_id = data['player_id']
                player_name = data.get('player_name', f"Player #{player_id}")
                game = data['game']
                
                if player_id not in player_totals:
                    player_totals[player_id] = {
                        'player_id': player_id,
                        'player_name': player_name,
                        'wins': 0,
                        'losses': 0,
                        'draws': 0,
                        'total_games': 0,
                        'games': {}  # Store individual game stats
                    }
                
                # Store individual game stats
                player_totals[player_id]['games'][game] = {
                    'wins': data.get('wins', 0),
                    'losses': data.get('losses', 0),
                    'draws': data.get('draws', 0),
                    'total_games': data.get('total_games', 0)
                }
                
                # Add this game's stats to the total
                player_totals[player_id]['wins'] += data.get('wins', 0)
                player_totals[player_id]['losses'] += data.get('losses', 0)
                player_totals[player_id]['draws'] += data.get('draws', 0)
                player_totals[player_id]['total_games'] += data.get('total_games', 0)
            
            # Convert to list and calculate win rates
            leaderboard = []
            for player_data in player_totals.values():
                if player_data['total_games'] > 0:  # Only include players with games
                    win_rate = (player_data['wins'] / player_data['total_games']) * 100
                    player_data['win_rate'] = round(win_rate, 1)
                    leaderboard.append(player_data)
            
            # Sort by wins (descending), then by win rate (descending)
            leaderboard.sort(key=lambda x: (x['wins'], x['win_rate']), reverse=True)
            
            return leaderboard[:limit]
            
        except Exception as e:
            print(f"Error getting overall leaderboard: {e}")
            return []

    def get_user_stats(self, user_id: int, game: str = None) -> Dict:
        """Get statistics for a specific user"""
        try:
            if game:
                # Get stats for specific game
                stats_ref = self.db.collection('player_stats').document(f"{user_id}_{game}")
                stats = stats_ref.get()
                
                if stats.exists:
                    data = stats.to_dict()
                    win_rate = (data['wins'] / data['total_games']) * 100 if data['total_games'] > 0 else 0
                    return {**data, 'win_rate': round(win_rate, 1)}
                else:
                    return {
                        'player_id': user_id,
                        'game': game,
                        'wins': 0,
                        'losses': 0,
                        'draws': 0,
                        'total_games': 0,
                        'win_rate': 0
                    }
            else:
                # Get stats for all games
                stats = self.db.collection('player_stats').where(
                    'player_id', '==', user_id
                ).stream()
                
                all_stats = {}
                for doc in stats:
                    data = doc.to_dict()
                    game_name = data['game']
                    win_rate = (data['wins'] / data['total_games']) * 100 if data['total_games'] > 0 else 0
                    all_stats[game_name] = {**data, 'win_rate': round(win_rate, 1)}
                    
                return all_stats
                
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {}

    def get_active_challenges(self, user_id: int) -> List[Dict]:
        """Get all active challenges for a user (accepted but not completed)"""
        try:
            challenges = self.db.collection('challenges').where(
                filter=firestore.FieldFilter('status', '==', 'accepted')
            ).where(
                filter=firestore.FieldFilter('challenger_id', '==', user_id)
            ).stream()
            
            opponent_challenges = self.db.collection('challenges').where(
                filter=firestore.FieldFilter('status', '==', 'accepted')
            ).where(
                filter=firestore.FieldFilter('opponent_id', '==', user_id)
            ).stream()
            
            active_challenges = []
            
            for doc in challenges:
                active_challenges.append({"id": doc.id, **doc.to_dict()})
                
            for doc in opponent_challenges:
                active_challenges.append({"id": doc.id, **doc.to_dict()})
                
            return active_challenges
            
        except Exception as e:
            print(f"Error getting active challenges: {e}")
            return []

    def cancel_challenge(self, challenge_id: str, user_id: int) -> bool:
        """Cancel a challenge (only challenger can cancel)"""
        try:
            challenge_ref = self.db.collection('challenges').document(challenge_id)
            challenge = challenge_ref.get()
            
            if not challenge.exists:
                return False
                
            challenge_data = challenge.to_dict()
            if challenge_data['challenger_id'] != user_id:
                return False
                
            if challenge_data['status'] != 'pending':
                return False
                
            challenge_ref.update({
                'status': 'cancelled',
                'completed_at': datetime.now()
            })
            return True
            
        except Exception as e:
            print(f"Error cancelling challenge: {e}")
            return False
