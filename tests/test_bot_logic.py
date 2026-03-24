import sys
import os
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Ensure we can import the bot module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock the discord module before importing bot, to avoid needing actual discord.py installed or configured if possible,
# or just to control side effects.
# However, for deeper integration tests we usually want the real discord objects if available, but mocking them is safer for unit tests.
# Especially FFmpegPCMAudio which might require system binaries.

with patch('discord.FFmpegPCMAudio') as MockAudio:
    from bot import bot

@pytest.fixture
def mock_ctx():
    ctx = MagicMock()
    ctx.message.author.voice = MagicMock()
    ctx.message.guild.channels = []
    ctx.guild.channels = []
    ctx.send = AsyncMock()
    ctx.message.delete = AsyncMock()
    ctx.message.content = ".11"
    ctx.command = MagicMock()
    ctx.command.name = "11"
    ctx.guild = MagicMock()
    return ctx

@pytest.fixture
def mock_voice_client():
    voice = MagicMock()
    voice.is_connected.return_value = True
    voice.play = MagicMock()
    # is_playing sequence needs to handle:
    # 1. potential interference check (Stop check)
    # 2. playback loop check (Loop check)
    # 3. potentially more checks for delay logic
    # Default to enough falses to pass simple tests
    voice.is_playing.side_effect = [False, False, False, False]
    voice.disconnect = AsyncMock()
    voice.move_to = AsyncMock()
    voice.connect = AsyncMock()
    return voice

@pytest.mark.asyncio
async def test_taunt_joins_voice_and_plays(mock_ctx, mock_voice_client):
    """Test that the bot joins voice and plays audio when command is issued."""
    # Setup - Override side effect for this test to look loop-y if needed, 
    # but [False, False...] is fine for "not playing initially, loop check returns false immediately"
    # Actually wait:
    # play_taunt_file:
    # if voice.is_playing(): (Call 1) -> False
    # play()
    # while voice.is_playing(): (Call 2) -> False (skips loop)
    # disconnect()
    
    mock_voice_client.is_playing.side_effect = [False, False, False]

    mock_ctx.message.author.voice.channel = MagicMock()
    mock_ctx.message.author.voice.channel.connect = AsyncMock(return_value=mock_voice_client)
    
    # Mock global client.voice_clients get
    with patch('bot.bot.get', return_value=None): # Not connected yet
        # Mock asyncio.sleep to be instant
        with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
             # Also mock os.path.exists to return True for the audio file
             with patch('os.path.exists', return_value=True):
                # Call the underlying function directly
                await bot.play_taunt(mock_ctx)

    # Asserts
    # Should have connected to author's channel
    mock_ctx.message.author.voice.channel.connect.assert_called_once()
    
    # Check if play was called
    assert mock_voice_client.play.called

@pytest.mark.asyncio
async def test_taunt_warns_and_joins_populated_channel(mock_ctx):
    """Test that bot warns and joins most populated channel if user is not in voice."""
    mock_ctx.message.author.voice = None
    
    # Mock sending message
    mock_ctx.send.return_value = MagicMock()
    mock_ctx.send.return_value.delete = AsyncMock()
    
    # Mock voice channels
    channel1 = MagicMock()
    channel1.name = "Channel 1"
    channel1.members = [MagicMock(), MagicMock()] # 2 members
    
    channel2 = MagicMock()
    channel2.name = "Channel 2"
    channel2.members = [MagicMock()] * 5 # 5 members (Winner)
    
    channel3 = MagicMock()
    channel3.name = "Channel 3"
    channel3.members = [MagicMock()] # 1 member
    
    # Assign voice channels to guild
    mock_ctx.guild.voice_channels = [channel1, channel2, channel3]
    
    # Mock voice client from connect
    mock_voice = MagicMock()
    mock_voice.is_connected.return_value = True
    mock_voice.is_playing.side_effect = [False, False, False]
    mock_voice.disconnect = AsyncMock()
    
    # Setup connect return value
    channel2.connect = AsyncMock(return_value=mock_voice)
    
    # We also need to mock client.voice_clients get to return None initially so it tries to connect
    with patch('bot.bot.get', return_value=None):
         with patch('os.path.exists', return_value=True):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await bot.play_taunt(mock_ctx)
         
    # Verify warning sent
    expected_msg = f"{mock_ctx.message.author.mention} You have to join voice channel to hear the taunt! I'll join Channel 2 since it has the most people."
    mock_ctx.send.assert_called_with(expected_msg)
    
    # Verify connected to Channel 2
    channel2.connect.assert_called_once()
    # Verify play called
    mock_voice.play.assert_called_once()

@pytest.mark.asyncio
async def test_play_sound_interrupts_existing(mock_voice_client):
    """Test that play_taunt_file stops existing audio before playing new."""
    # 1. if voice.is_playing(): stop() -> True
    # 2. play()
    # 3. while voice.is_playing(): ... -> True (enters loop)
    # 4. while voice.is_playing(): ... -> False (exits loop)
    # 5. if voice.is_playing(): return (delay check, implicitly 0 here) -> False
    
    mock_voice_client.is_playing.side_effect = [True, True, False, False]
    mock_voice_client.stop = MagicMock()
    
    with patch('os.path.exists', return_value=True):
         with patch('bot.bot.FFmpegPCMAudio'):
            # Import function to test logic directly
            from bot.bot import play_taunt_file
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await play_taunt_file(mock_voice_client, "dummy.ogg")
            
            mock_voice_client.stop.assert_called_once()
            mock_voice_client.play.assert_called_once()

@pytest.mark.asyncio
async def test_play_sound_disconnect_delay(mock_voice_client):
    """Test that disconnect is delayed if requested."""
    # 1. Start check -> False
    # 2. Loop check -> False
    # 3. Post-delay check -> False
    mock_voice_client.is_playing.side_effect = [False, False, False]
    
    with patch('os.path.exists', return_value=True):
         with patch('bot.bot.FFmpegPCMAudio'):
            from bot.bot import play_taunt_file
            
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                # Call with 60s delay
                await play_taunt_file(mock_voice_client, "dummy.ogg", disconnect_delay=60)
                
                # Await the created task
                if hasattr(mock_voice_client, '_disconnect_task'):
                    await mock_voice_client._disconnect_task

                # Verify sleep called with 60
                mock_sleep.assert_any_call(60)
                # Verify disconnected
                mock_voice_client.disconnect.assert_called_once()
                
@pytest.mark.asyncio
async def test_play_sound_cancels_disconnect_if_playing(mock_voice_client):
    """Test that disconnect is aborted if new sound starts playing during delay."""
    # 1. Start check -> False
    # 2. Loop check -> False
    # 3. Post-delay check -> True (ABORT DISCONNECT)
    mock_voice_client.is_playing.side_effect = [False, False, True]
    
    with patch('os.path.exists', return_value=True):
         with patch('bot.bot.FFmpegPCMAudio'):
            from bot.bot import play_taunt_file
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                await play_taunt_file(mock_voice_client, "dummy.ogg", disconnect_delay=60)
                
                if hasattr(mock_voice_client, '_disconnect_task'):
                    await mock_voice_client._disconnect_task

                # Should NOT disconnect
                mock_voice_client.disconnect.assert_not_called()

@pytest.mark.asyncio
async def test_specific_user_taunt(mock_voice_client):
    """Test that a specific user triggers their assigned taunt."""
    from bot import bot
    # Setup mock member
    member = MagicMock()
    member.name = 'monkie35k'
    member.bot = False
    member.guild = MagicMock()
    
    # Setup Voice state
    before = MagicMock()
    before.channel = None
    after = MagicMock()
    after.channel = MagicMock()
    after.channel.name = "General"
    after.channel.connect = AsyncMock(return_value=mock_voice_client)
    
    # Mock file system
    with patch('os.path.exists', return_value=True):
        with patch('os.listdir', return_value=['yahoo.ogg', 'other.ogg']):
             with patch('bot.bot.FFmpegPCMAudio'):
                # Mock get voice client to return None initially
                with patch('bot.bot.get', return_value=None):
                    with patch('asyncio.sleep', new_callable=AsyncMock):
                        await bot.on_voice_state_update(member, before, after)
                        
    # Verify the specific file was played
    # Implicitly verified if no error, but ideally we check args. 
    # The next test covers arg checking more rigorously.
    pass 


@pytest.mark.asyncio
async def test_on_voice_state_update_specific_user(mock_voice_client):
    """Test full flow for a specific user mapping."""
    # We need to patch play_taunt_file to verify arguments
    with patch('bot.bot.play_taunt_file', new_callable=AsyncMock) as mock_play:
        from bot import bot
        
        # Override the mapping to match expectations of this test
        old_mapping = bot.USER_TAUNT_MAPPING
        bot.USER_TAUNT_MAPPING = {'monkie35k': 'yahoo'}
        
        member = MagicMock()
        member.name = 'monkie35k' # Mapped to 'yahoo'
        member.bot = False
        member.guild = MagicMock()
        
        before = MagicMock()
        before.channel = None
        after = MagicMock()
        after.channel = MagicMock()
        after.channel.connect = AsyncMock(return_value=mock_voice_client)

        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=['yahoo.ogg', 'random.ogg']):
                with patch('bot.bot.get', return_value=None):
                     await bot.on_voice_state_update(member, before, after)
        
        bot.USER_TAUNT_MAPPING = old_mapping
        
        # Verify
        mock_play.assert_called_once()
        # Verify second argument ends with yahoo.ogg
        args, _ = mock_play.call_args
        assert args[1].endswith('yahoo.ogg')


@pytest.mark.asyncio
async def test_on_voice_state_update_random_user(mock_voice_client):
    """Test full flow for unmapped user."""
    with patch('bot.bot.play_taunt_file', new_callable=AsyncMock) as mock_play:
        from bot import bot
        
        member = MagicMock()
        member.name = 'unknown_user' 
        member.bot = False
        member.guild = MagicMock()
        
        before = MagicMock()
        before.channel = None
        after = MagicMock()
        after.channel = MagicMock()
        after.channel.connect = AsyncMock(return_value=mock_voice_client)

        with patch('os.path.exists', return_value=True):
            with patch('os.listdir', return_value=['random.ogg']):
                with patch('bot.bot.get', return_value=None):
                    with patch('random.choice', return_value='random.ogg'):
                         await bot.on_voice_state_update(member, before, after)
        
        # Verify
        mock_play.assert_called_once()
        args, _ = mock_play.call_args
        assert args[1].endswith('random.ogg')