import asyncio
from google.cloud import speech
import open_ai_chat
import time


async def transcribe_stream(audio_stream, webrtcdatachannel):

    open_ai_key = "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"

    open_ai_client = open_ai_chat.OpenAIChat(open_ai_key)
    print("transcribing the stream")
    client = speech.SpeechAsyncClient.from_service_account_file('key.json')
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=16000,
        language_code="en-US",
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

    # Initialize a request generator
    async def request_generator(audio_stream):
        yield speech.StreamingRecognizeRequest(
            streaming_config=streaming_config,
        )
        while True:
            content = await audio_stream.__anext__()
            yield speech.StreamingRecognizeRequest(audio_content=content)

    # Make the streaming recognize request
    requests = request_generator(audio_stream).__aiter__()
    response = await client.streaming_recognize(requests=requests)

    # print(response)

    # return True
    kl = 0

    final_response = []

    def make_string(final_response):
        string = ""
        for i in final_response:
            string = string + i + " "
        return string

    def remove_duplicates(final_response):
        if(len(final_response) > 1):
            if final_response[-2] in final_response[-1]:
                final_response[-2] = final_response[-1]
                final_response.pop()
                remove_duplicates(final_response)

    async def abcd(transcription):
        open_ai_client.add_user_message(transcription)
        ai_response = open_ai_client.call_openai()
        if(webrtcdatachannel.channel is not None):
            webrtcdatachannel.channel.send(ai_response)
        # final_response.clear()


    async for i in response:
        final_response.append(i.results[0].alternatives[0].transcript)
        remove_duplicates(final_response)

        print(f"{i.results[0].alternatives[0].transcript}" )
        kl = kl + 1
        if(kl % 20 == 0):
            transcription = make_string(final_response)
            print(transcription)
            asyncio.create_task(abcd(transcription))
            final_response.clear()
            # return transcription
        
