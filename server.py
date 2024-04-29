import argparse
import asyncio
import json
import logging
import os
import aiohttp_cors
import av

from aiohttp import web
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder
from aiortc import  MediaStreamTrack
from aiortc.contrib.media import MediaRelay  # Ensure this line is added
import numpy as np

from speech_to_text import transcribe_stream


logger = logging.getLogger("pc")
pcs = set()

webrtcdatachannel = None

output = av.open('dash.mp3', 'w')
stream = output.add_stream('mp3')


class DataConnection:
    channel = None

class Interview:
    def __init__(self):
        self.is_interview_active = True


interview = Interview()
def channel_log(channel, t, message):
    print("channel(%s) %s %s" % (channel.label, t, message))


def channel_send(channel, message):
    channel_log(channel, ">", message)
    channel.send(message)


async def offer(request):
    print("offer started")
    params = await request.json()
    sdp = params.get("sdp")
    type_ = params.get("type")

    if not sdp or not type_:
        return web.Response(status=400, text="Missing SDP or type in request")

    offer = RTCSessionDescription(sdp=sdp, type=type_)

    pc = RTCPeerConnection()
    
    webrtcdatachannel = DataConnection()
    pc_id = f"PeerConnection({id(pc)})"
    pcs.add(pc)

    @pc.on("datachannel")
    async def on_datachannel(channel):
        webrtcdatachannel.channel = channel

    logger.info(f"{pc_id} Created for {request.remote}")

    print("\n\n media relay time")

    relay = MediaRelay()

    @pc.on("track")
    async def on_track(track):
        print("\n\n\n\n")
        print("track is running")
        print("\n\n\n\n")
        if track.kind == "audio":
            logger.info(f"{pc_id} Audio track received")
            relayed_track = relay.subscribe(track)
            asyncio.create_task(transcribe_stream(audio_generator(relayed_track), webrtcdatachannel, interview))
    async def start_listening(ag):
        while True:
            print(await ag.__anext__())

    async def audio_generator(audio_track):
    # Assuming you have a method to fetch frames from the audio track
        while True:
            frame = await audio_track.recv()
            if not frame:
                break
            encoded_frame = stream.encode(frame)
            if len(encoded_frame) > 0:
                yield encoded_frame[0].to_bytes()
              # Convert the frame to bytes

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps({"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}),
    )

# Include the rest of your existing code setup here



async def on_shutdown(app):
    print("shutdown is called")
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()
    interview.is_interview_active = False

# In your main section after setting up the app
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WebRTC audio recorder")
    parser.add_argument("--port", type=int, default=8080, help="Port for HTTP server (default: 8080)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    app = web.Application()
    interview = Interview()
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
