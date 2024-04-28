import asyncio
from google.cloud import speech

async def transcribe_stream(audio_stream):
    client = speech.SpeechClient.from_service_account_file('key.json')
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44000,
        language_code="en-US",
    )
    streaming_config = speech.StreamingRecognitionConfig(config=config, interim_results=True)

    # Initialize a request generator
    async def request_generator(audio_stream):
        for audio_content in audio_stream:
            yield speech.StreamingRecognizeRequest(audio_content = await audio_content)

    # Make the streaming recognize request
    requests = request_generator(audio_stream)
    responses = client.streaming_recognize(streaming_config, requests)

    # Process responses
    try:
        for response in responses:
            for result in response.results:
                print("Transcript: {}".format(result.alternatives[0].transcript))
    except Exception as e:
        print("Error processing stream: {}".format(str(e)))
