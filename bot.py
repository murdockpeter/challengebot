import discord
from discord.ext import commands
import asyncio
from typing import Optional
import config
from database import ChallengeDatabase

class ChallengeBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix=config.COMMAND_PREFIX,
            intents=intents,
            help_command=None
        )
        
        self.db = ChallengeDatabase()
        
    async def setup_hook(self):
        """Setup hook to load cogs and prepare the bot"""
        print("Setting up ChallengeBot...")
        
    async def on_ready(self):
        """Called when the bot is ready"""
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} guild(s)')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Game(name="!help for commands")
        )

class ChallengeCommands(commands.Cog):
    def __init__(self, bot: ChallengeBot):
        self.bot = bot
        self.db = bot.db

    @commands.command(name='challenge')
    async def challenge(self, ctx, opponent: discord.Member, *, game: str):
        """Challenge another player to a board game"""
        if opponent.bot:
            await ctx.send("❌ You cannot challenge a bot!")
            return
            
        if opponent.id == ctx.author.id:
            await ctx.send("❌ You cannot challenge yourself!")
            return
            
        if game not in config.SUPPORTED_GAMES:
            games_list = ", ".join(config.SUPPORTED_GAMES)
            await ctx.send(f"❌ Unsupported game! Supported games: {games_list}")
            return
            
        try:
            challenge_id = self.db.create_challenge(
                challenger_id=ctx.author.id,
                challenger_name=ctx.author.display_name,
                opponent_id=opponent.id,
                opponent_name=opponent.display_name,
                game=game
            )
            
            embed = discord.Embed(
                title="🎮 New Challenge!",
                description=f"{ctx.author.mention} has challenged {opponent.mention} to a game of **{game}**!",
                color=discord.Color.blue()
            )
            embed.add_field(name="Game", value=game, inline=True)
            embed.add_field(name="Status", value="⏳ Pending", inline=True)
            embed.add_field(name="Challenge ID", value=challenge_id, inline=False)
            embed.add_field(name="To Accept", value=f"Use `!accept {challenge_id}`", inline=False)
            embed.set_footer(text=f"Challenge created by {ctx.author.display_name}")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error creating challenge: {str(e)}")

    @commands.command(name='accept')
    async def accept(self, ctx, challenge_id: str):
        """Accept a pending challenge"""
        try:
            success = self.db.accept_challenge(challenge_id, ctx.author.id)
            
            if success:
                # Get challenge details for the embed
                pending_challenges = self.db.get_pending_challenges_for_user(ctx.author.id)
                challenge = next((c for c in pending_challenges if c['id'] == challenge_id), None)
                
                if challenge:
                    embed = discord.Embed(
                        title="✅ Challenge Accepted!",
                        description=f"{ctx.author.mention} has accepted the challenge!",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Game", value=challenge['game'], inline=True)
                    embed.add_field(name="Challenger", value=challenge['challenger_name'], inline=True)
                    embed.add_field(name="Status", value="🎯 Active", inline=True)
                    embed.add_field(name="To Report Result", value=f"Use `!report {challenge_id} <win/loss/draw> <winner_id>`", inline=False)
                    embed.set_footer(text=f"Challenge accepted by {ctx.author.display_name}")
                    
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("✅ Challenge accepted!")
            else:
                await ctx.send("❌ Failed to accept challenge. Make sure you're the intended opponent and the challenge is still pending.")
                
        except Exception as e:
            await ctx.send(f"❌ Error accepting challenge: {str(e)}")

    @commands.command(name='report')
    async def report(self, ctx, challenge_id: str, result: str, winner_id: Optional[int] = None):
        """Report the result of a completed game"""
        if result not in ['win', 'loss', 'draw']:
            await ctx.send("❌ Result must be 'win', 'loss', or 'draw'")
            return
            
        try:
            # Get active challenges to find the challenge
            active_challenges = self.db.get_active_challenges(ctx.author.id)
            challenge = next((c for c in active_challenges if c['id'] == challenge_id), None)
            
            if not challenge:
                await ctx.send("❌ Challenge not found or not active. Make sure you're part of the challenge and it's been accepted.")
                return
                
            # Determine winner and loser IDs
            winner_id_final = None
            loser_id_final = None
            
            if result == 'win':
                if winner_id:
                    winner_id_final = winner_id
                    loser_id_final = challenge['challenger_id'] if winner_id == challenge['opponent_id'] else challenge['opponent_id']
                else:
                    winner_id_final = ctx.author.id
                    loser_id_final = challenge['challenger_id'] if ctx.author.id == challenge['opponent_id'] else challenge['opponent_id']
            elif result == 'loss':
                if winner_id:
                    winner_id_final = winner_id
                    loser_id_final = ctx.author.id
                else:
                    winner_id_final = challenge['challenger_id'] if ctx.author.id == challenge['opponent_id'] else challenge['opponent_id']
                    loser_id_final = ctx.author.id
            # For draw, both winner_id and loser_id remain None
            
            success = self.db.report_result(
                challenge_id=challenge_id,
                reporter_id=ctx.author.id,
                result=result,
                winner_id=winner_id_final,
                loser_id=loser_id_final
            )
            
            if success:
                embed = discord.Embed(
                    title="🏆 Game Result Reported!",
                    description=f"Result for **{challenge['game']}** has been recorded.",
                    color=discord.Color.gold()
                )
                embed.add_field(name="Game", value=challenge['game'], inline=True)
                embed.add_field(name="Result", value=result.upper(), inline=True)
                
                if result == 'win':
                    winner_name = challenge['challenger_name'] if winner_id_final == challenge['challenger_id'] else challenge['opponent_name']
                    loser_name = challenge['challenger_name'] if loser_id_final == challenge['challenger_id'] else challenge['opponent_name']
                    embed.add_field(name="Winner", value=winner_name, inline=True)
                    embed.add_field(name="Loser", value=loser_name, inline=True)
                elif result == 'loss':
                    winner_name = challenge['challenger_name'] if winner_id_final == challenge['challenger_id'] else challenge['opponent_name']
                    loser_name = challenge['challenger_name'] if loser_id_final == challenge['challenger_id'] else challenge['opponent_name']
                    embed.add_field(name="Winner", value=winner_name, inline=True)
                    embed.add_field(name="Loser", value=loser_name, inline=True)
                else:
                    embed.add_field(name="Outcome", value="Draw", inline=True)
                
                embed.set_footer(text=f"Result reported by {ctx.author.display_name}")
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Failed to report result. Make sure you're part of the challenge and it's been accepted.")
                
        except Exception as e:
            await ctx.send(f"❌ Error reporting result: {str(e)}")

    @commands.command(name='leaderboard')
    async def leaderboard(self, ctx, game: str = None):
        """Show leaderboard for a specific game or overall"""
        if game and game not in config.SUPPORTED_GAMES:
            games_list = ", ".join(config.SUPPORTED_GAMES)
            await ctx.send(f"❌ Unsupported game! Supported games: {games_list}")
            return
            
        try:
            if game:
                leaderboard = self.db.get_leaderboard(game)
                
                if not leaderboard:
                    await ctx.send(f"No statistics available for {game} yet!")
                    return
                    
                embed = discord.Embed(
                    title=f"🏆 {game} Leaderboard",
                    description="Top players by wins",
                    color=discord.Color.gold()
                )
                
                for i, player in enumerate(leaderboard[:10], 1):
                    player_display_name = player.get('player_name', f"Player #{player['player_id']}")
                    embed.add_field(
                        name=f"#{i} {player_display_name}",
                        value=f"Wins: {player['wins']} | Losses: {player['losses']} | Win Rate: {player['win_rate']}%",
                        inline=False
                    )
                    
                await ctx.send(embed=embed)
            else:
                # Show overall leaderboard across all games
                overall_leaderboard = self.db.get_overall_leaderboard()
                
                if not overall_leaderboard:
                    embed = discord.Embed(
                        title="🏆 Overall Leaderboard",
                        description="No statistics available yet!",
                        color=discord.Color.gold()
                    )
                    embed.add_field(
                        name="Available Games",
                        value=", ".join(config.SUPPORTED_GAMES),
                        inline=False
                    )
                    embed.add_field(
                        name="Get Started",
                        value="Challenge someone to start building the leaderboard!",
                        inline=False
                    )
                    await ctx.send(embed=embed)
                    return
                
                embed = discord.Embed(
                    title="🏆 Overall Leaderboard",
                    description="Top players across all games combined",
                    color=discord.Color.gold()
                )
                
                for i, player in enumerate(overall_leaderboard[:10], 1):
                    # Build overall stats line
                    overall_line = f"**Total:** {player['wins']}W-{player['losses']}L-{player['draws']}D (Win Rate: {player['win_rate']}%)\n"
                    
                    # Build game breakdown
                    game_breakdown = []
                    for game_name, game_stats in player['games'].items():
                        if game_stats['total_games'] > 0:  # Only show games they've played
                            game_line = f"├ **{game_name}**: {game_stats['wins']}W-{game_stats['losses']}L-{game_stats['draws']}D"
                            game_breakdown.append(game_line)
                    
                    # Join with newlines, replace last ├ with └
                    if game_breakdown:
                        game_breakdown[-1] = game_breakdown[-1].replace('├', '└')
                        breakdown_text = '\n'.join(game_breakdown)
                        full_value = overall_line + breakdown_text
                    else:
                        full_value = overall_line
                    
                    embed.add_field(
                        name=f"#{i} {player['player_name']}",
                        value=full_value,
                        inline=False
                    )
                
                embed.add_field(
                    name="📊 Game-Specific Leaderboards",
                    value="Use `!leaderboard <game_name>` for individual game stats",
                    inline=False
                )
                
                await ctx.send(embed=embed)
                
        except Exception as e:
            await ctx.send(f"❌ Error getting leaderboard: {str(e)}")

    @commands.command(name='stats')
    async def stats(self, ctx, member: Optional[discord.Member] = None, game: str = None):
        """Show statistics for yourself or another player"""
        target_member = member or ctx.author
        
        try:
            stats = self.db.get_user_stats(target_member.id, game)
            
            if game:
                if not stats:
                    await ctx.send(f"No statistics available for {target_member.display_name} in {game}")
                    return
                    
                embed = discord.Embed(
                    title=f"📊 {target_member.display_name}'s {game} Stats",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Wins", value=stats['wins'], inline=True)
                embed.add_field(name="Losses", value=stats['losses'], inline=True)
                embed.add_field(name="Draws", value=stats['draws'], inline=True)
                embed.add_field(name="Total Games", value=stats['total_games'], inline=True)
                embed.add_field(name="Win Rate", value=f"{stats['win_rate']}%", inline=True)
                
            else:
                if not stats:
                    await ctx.send(f"No statistics available for {target_member.display_name}")
                    return
                    
                embed = discord.Embed(
                    title=f"📊 {target_member.display_name}'s Statistics",
                    color=discord.Color.blue()
                )
                
                for game_name, game_stats in stats.items():
                    embed.add_field(
                        name=game_name,
                        value=f"W: {game_stats['wins']} L: {game_stats['losses']} D: {game_stats['draws']} ({game_stats['win_rate']}%)",
                        inline=True
                    )
                    
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error getting stats: {str(e)}")

    @commands.command(name='challenges')
    async def challenges(self, ctx):
        """Show pending and active challenges for the user"""
        try:
            pending_challenges = self.db.get_pending_challenges_for_user(ctx.author.id)
            active_challenges = self.db.get_active_challenges(ctx.author.id)
            
            if not pending_challenges and not active_challenges:
                await ctx.send("You have no pending or active challenges!")
                return
                
            embed = discord.Embed(
                title="🎮 Your Challenges",
                color=discord.Color.blue()
            )
            
            if pending_challenges:
                pending_text = ""
                for challenge in pending_challenges:
                    if challenge['challenger_id'] == ctx.author.id:
                        # User sent this challenge
                        pending_text += f"**{challenge['game']}** - Challenged {challenge['opponent_name']} (ID: {challenge['id']})\n"
                    else:
                        # User received this challenge
                        pending_text += f"**{challenge['game']}** - Challenged by {challenge['challenger_name']} (ID: {challenge['id']})\n"
                embed.add_field(name="⏳ Pending", value=pending_text, inline=False)
                
            if active_challenges:
                active_text = ""
                for challenge in active_challenges:
                    active_text += f"**{challenge['game']}** - vs {challenge['opponent_name'] if challenge['challenger_id'] == ctx.author.id else challenge['challenger_name']} (ID: {challenge['id']})\n"
                embed.add_field(name="🎯 Active", value=active_text, inline=False)
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error getting challenges: {str(e)}")

    @commands.command(name='cancel')
    async def cancel(self, ctx, challenge_id: str):
        """Cancel a pending challenge (only challenger can cancel)"""
        try:
            success = self.db.cancel_challenge(challenge_id, ctx.author.id)
            
            if success:
                await ctx.send("✅ Challenge cancelled successfully!")
            else:
                await ctx.send("❌ Failed to cancel challenge. Make sure you're the challenger and the challenge is still pending.")
                
        except Exception as e:
            await ctx.send(f"❌ Error cancelling challenge: {str(e)}")

    @commands.command(name='games')
    async def games(self, ctx):
        """Show all supported games"""
        embed = discord.Embed(
            title="🎮 Supported Games",
            description="Here are all the games you can challenge others to:",
            color=discord.Color.green()
        )
        
        games_text = "\n".join([f"• {game}" for game in config.SUPPORTED_GAMES])
        embed.add_field(name="Available Games", value=games_text, inline=False)
        embed.add_field(name="Usage", value="Use `!challenge @player <game_name>` to challenge someone!", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command(name='help')
    async def help_command(self, ctx):
        """Show help information"""
        embed = discord.Embed(
            title="🎮 ChallengeBot Help",
            description="A Discord bot for managing board game challenges and tracking statistics!",
            color=discord.Color.purple()
        )
        
        commands_info = [
            ("!challenge @player <game>", "Challenge another player to a board game"),
            ("!accept <challenge_id>", "Accept a pending challenge"),
            ("!report <challenge_id> <win/loss/draw> [winner_id]", "Report the result of a completed game"),
            ("!leaderboard <game>", "Show leaderboard for a specific game"),
            ("!stats [@player] [game]", "Show statistics for yourself or another player"),
            ("!challenges", "Show your pending and active challenges"),
            ("!cancel <challenge_id>", "Cancel a pending challenge (challenger only)"),
            ("!games", "Show all supported games"),
            ("!help", "Show this help message")
        ]
        
        for cmd, desc in commands_info:
            embed.add_field(name=cmd, value=desc, inline=False)
            
        embed.set_footer(text="ChallengeBot - Making board game challenges fun and easy!")
        
        await ctx.send(embed=embed)

async def main():
    """Main function to run the bot"""
    bot = ChallengeBot()
    
    # Add the commands cog
    await bot.add_cog(ChallengeCommands(bot))
    
    # Run the bot
    await bot.start(config.DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
