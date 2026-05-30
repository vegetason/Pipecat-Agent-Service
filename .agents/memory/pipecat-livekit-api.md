---
name: Pipecat 1.3 LiveKit transport API
description: Correct event names and runner methods for pipecat 1.3 LiveKit transport
---

## LiveKit transport event names (pipecat 1.3)

Register via `@transport.event_handler("name")`. All handlers receive `*args` (first arg is usually participant_id string).

| Event | When it fires |
|---|---|
| `on_first_participant_joined` | First remote participant connects — use this to unblock the agent |
| `on_participant_connected` | Any remote participant connects |
| `on_participant_left` | Remote participant leaves (fires on disconnect) |
| `on_participant_disconnected` | Also fires on disconnect |
| `on_bot_started_speaking` | TTS audio starts playing |
| `on_bot_stopped_speaking` | TTS audio finishes playing |
| `on_connected` | Transport connects to LiveKit server |
| `on_disconnected` | Transport disconnects |

**Why:** `on_participant_joined` does NOT exist — it silently never fires, causing the participant_joined event to never be set and the interview to time out after 300s.

## PipelineRunner / WorkerRunner (pipecat 1.3)

`PipelineRunner` is a deprecated alias for `WorkerRunner` (from `pipecat.workers.runner`).

Correct method to stop the pipeline from an event handler:
```python
await runner.cancel()          # WorkerRunner.cancel(reason=None)
```
`runner.stop()` does NOT exist — raises AttributeError.

**Why:** The old `runner.stop()` caused on_participant_left to crash silently (pipecat logs the error but doesn't re-raise), leaving the pipeline orphaned until idle timeout.
