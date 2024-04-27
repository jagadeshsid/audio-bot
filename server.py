import argparse
import asyncio
import json
import logging
import os
import aiohttp_cors

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder

from speech_to_text import transcribe  # Importing the transcribe function

logger = logging.getLogger("pc")
pcs = set()

async def offer(request):
    try:
        params = await request.json()
        sdp = params.get("sdp")
        type_ = params.get("type")

        if not sdp or not type_:
            return web.Response(status=400, text="Missing SDP or type in request")

        offer = RTCSessionDescription(sdp=sdp, type=type_)

        pc = RTCPeerConnection()
        pc_id = f"PeerConnection({id(pc)})"
        pcs.add(pc)

        logger.info(f"{pc_id} Created for {request.remote}")

        # Specify the audio file path here
        audio_file_path = os.getenv('AUDIO_RECORD_PATH', 'output.mp3')
        recorder = MediaRecorder(audio_file_path)

        @pc.on("track")
        def on_track(track):
            logger.info(f"{pc_id} Track {track.kind} received")
            if track.kind == "audio":
                recorder.addTrack(track)

            @track.on("ended")
            async def on_ended():
                logger.info(f"{pc_id} Track {track.kind} ended")
                await recorder.stop()
                # Transcribe the audio file after recording
                transcription = transcribe(audio_file_path)
                print("Transcription:", transcription)

        await pc.setRemoteDescription(offer)
        await recorder.start()

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return web.Response(
            content_type="application/json",
            text=json.dumps(
                {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
            ),
        )
    except Exception as e:
        logger.error("Failed to handle offer: %s", str(e))
        return web.Response(status=500, text=str(e))

async def on_shutdown(app):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WebRTC audio recorder")
    parser.add_argument("--port", type=int, default=8999, help="Port for HTTP server (default: 8080)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_post("/offer", offer)

    # Setup CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
    })

    # Configure CORS on all routes
    for route in list(app.router.routes()):
        cors.add(route)

    web.run_app(app, port=args.port)
