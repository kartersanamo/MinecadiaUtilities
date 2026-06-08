"""Temporary voice recording — /record start and /record stop."""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands, voice_recv
from discord.opus import Decoder as OpusDecoder

log = logging.getLogger("Record")

try:
    discord.opus._load_default()  # type: ignore[attr-defined]
except Exception:
    pass

# One silent Opus frame (stereo 48kHz) — used when a packet fails to decode.
_SILENCE_PCM = b"\x00" * OpusDecoder.FRAME_SIZE


def _apply_voice_recv_patches() -> None:
    """OpusError kills PacketRouter and stops recording; patch around that (discord.py 2.7)."""
    from discord.ext.voice_recv import opus as vr_opus
    from discord.ext.voice_recv import router as vr_router

    if getattr(vr_router.PacketRouter, "_minecadia_patched", False):
        return

    _orig_decode = vr_opus.PacketDecoder._decode_packet

    def _decode_packet_safe(self, packet):  # type: ignore[no-untyped-def]
        try:
            return _orig_decode(self, packet)
        except Exception:
            return packet, _SILENCE_PCM

    vr_opus.PacketDecoder._decode_packet = _decode_packet_safe  # type: ignore[method-assign]

    def _do_run_safe(self) -> None:
        while not self._end_thread.is_set():
            self.waiter.wait()
            with self._lock:
                for decoder in self.waiter.items:
                    try:
                        data = decoder.pop_data()
                    except Exception:
                        continue
                    if data is not None:
                        self.sink.write(data.source, data)

    vr_router.PacketRouter._do_run = _do_run_safe  # type: ignore[method-assign]
    vr_router.PacketRouter._minecadia_patched = True
    log.info("Applied voice_recv Opus/router patches for recording")


_apply_voice_recv_patches()


def _wav_has_audio(path: Path, *, min_frames: int = 100) -> bool:
    """Skip empty/header-only wav files (produces 0s MP3)."""
    try:
        with wave.open(str(path), "rb") as wf:
            return wf.getnframes() >= min_frames
    except Exception:
        return False


class _PerUserWavSink(voice_recv.AudioSink):
    """One .wav per speaker; mixed to a single .mp3 on stop."""

    def __init__(self, directory: Path) -> None:
        super().__init__()
        self.directory = directory
        self._user_sinks: dict[int, voice_recv.WaveSink] = {}

    def wants_opus(self) -> bool:
        return False

    def write(self, user: Optional[discord.Member], data: voice_recv.VoiceData) -> None:
        if user is None:
            return
        uid = user.id
        if uid not in self._user_sinks:
            path = str(self.directory / f"{uid}.wav")
            sink = voice_recv.WaveSink(path)
            sink._voice_client = self.voice_client
            self._user_sinks[uid] = sink
        self._user_sinks[uid].write(user, data)

    def cleanup(self) -> None:
        for sink in self._user_sinks.values():
            sink.cleanup()


def _mix_to_mp3(wav_files: list[Path], out_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is not installed on this host.")

    if len(wav_files) == 1:
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(wav_files[0]),
            "-codec:a",
            "libmp3lame",
            "-qscale:a",
            "2",
            str(out_path),
        ]
    else:
        inputs: list[str] = []
        streams = []
        for i, wav in enumerate(wav_files):
            inputs.extend(["-i", str(wav)])
            streams.append(f"[{i}:a]")
        filter_complex = "".join(streams) + f"amix=inputs={len(wav_files)}:duration=longest[aout]"
        cmd = [
            ffmpeg,
            "-y",
            *inputs,
            "-filter_complex",
            filter_complex,
            "-map",
            "[aout]",
            "-codec:a",
            "libmp3lame",
            "-qscale:a",
            "2",
            str(out_path),
        ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-500:] if proc.stderr else "ffmpeg failed")


class Record(commands.Cog):
    record = app_commands.Group(
        name="record",
        description="Temporary: record voice chat (join on start, leave and upload MP3 on stop)",
    )

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._sessions: dict[int, dict] = {}

    def _session(self, guild_id: int) -> Optional[dict]:
        return self._sessions.get(guild_id)

    @record.command(name="start", description="Join your VC and start recording")
    async def start(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            return await interaction.response.send_message(
                "Use this in a server.", ephemeral=True
            )
        member = interaction.guild.get_member(interaction.user.id)
        if not member or not member.voice or not member.voice.channel:
            return await interaction.response.send_message(
                "Join a voice channel first.", ephemeral=True
            )
        if self._session(interaction.guild.id):
            return await interaction.response.send_message(
                "Already recording here. Use `/record stop` first.", ephemeral=True
            )

        await interaction.response.defer()

        guild = interaction.guild
        voice_channel = member.voice.channel
        text_channel = interaction.channel

        if guild.voice_client:
            await guild.voice_client.disconnect(force=True)

        tmpdir = Path(tempfile.mkdtemp(prefix=f"vc_rec_{guild.id}_"))
        sink = _PerUserWavSink(tmpdir)

        try:
            vc = await voice_channel.connect(
                cls=voice_recv.VoiceRecvClient,
                self_deaf=False,
            )
            vc.listen(sink)
        except Exception as exc:
            shutil.rmtree(tmpdir, ignore_errors=True)
            log.exception("record start failed")
            return await interaction.followup.send(
                f"Could not start recording: {exc}", ephemeral=True
            )

        self._sessions[guild.id] = {
            "vc": vc,
            "sink": sink,
            "tmpdir": tmpdir,
            "text_channel_id": text_channel.id if text_channel else None,
        }

        await interaction.followup.send(
            f"Recording in **{voice_channel.name}**. Run `/record stop` when finished."
        )

    @record.command(name="stop", description="Stop recording, leave VC, and upload the MP3")
    async def stop(self, interaction: discord.Interaction) -> None:
        if not interaction.guild:
            return await interaction.response.send_message(
                "Use this in a server.", ephemeral=True
            )

        session = self._sessions.pop(interaction.guild.id, None)
        if not session:
            return await interaction.response.send_message(
                "Not recording in this server. Use `/record start` first.", ephemeral=True
            )

        await interaction.response.defer()

        vc: voice_recv.VoiceRecvClient = session["vc"]
        sink: _PerUserWavSink = session["sink"]
        tmpdir: Path = session["tmpdir"]
        text_channel_id: Optional[int] = session.get("text_channel_id")

        try:
            if vc.is_listening():
                vc.stop_listening()
            sink.cleanup()
            if vc.is_connected():
                await vc.disconnect(force=True)
        except Exception:
            log.exception("record stop disconnect")

        wav_files = [p for p in sorted(tmpdir.glob("*.wav")) if _wav_has_audio(p)]
        out_mp3 = tmpdir / "recording.mp3"
        channel = interaction.channel
        if text_channel_id:
            ch = interaction.guild.get_channel(text_channel_id)
            if isinstance(ch, discord.TextChannel):
                channel = ch

        try:
            if not wav_files:
                await interaction.followup.send(
                    "Stopped. No usable audio was captured — speak in VC while recording "
                    "(the bot must hear you; check it is not server-deafened)."
                )
                return

            _mix_to_mp3(wav_files, out_mp3)
            await channel.send(
                "Recording finished.",
                file=discord.File(out_mp3, filename="voice_recording.mp3"),
            )
            await interaction.followup.send("Uploaded recording to this channel.")
        except Exception as exc:
            log.exception("record stop export failed")
            await interaction.followup.send(f"Stopped but could not create MP3: {exc}")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    async def cog_unload(self) -> None:
        for guild_id in list(self._sessions.keys()):
            session = self._sessions.pop(guild_id, None)
            if not session:
                continue
            vc = session.get("vc")
            sink = session.get("sink")
            tmpdir = session.get("tmpdir")
            try:
                if vc and vc.is_listening():
                    vc.stop_listening()
                if sink:
                    sink.cleanup()
                if vc and vc.is_connected():
                    await vc.disconnect(force=True)
            except Exception:
                pass
            if tmpdir:
                shutil.rmtree(tmpdir, ignore_errors=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Record(bot))
