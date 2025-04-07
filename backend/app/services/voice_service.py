import azure.cognitiveservices.speech as speechsdk
import io
from fastapi import UploadFile

class AzureVoiceService:
    def __init__(self):
        self.speech_key = "YOUR_SPEECH_KEY"
        self.service_region = "YOUR_SERVICE_REGION"

    async def speech_to_text(self, audio_file: UploadFile):
        speech_config = speechsdk.SpeechConfig(subscription=self.speech_key, region=self.service_region)
        audio_input = speechsdk.AudioConfig(filename=audio_file.file)

        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

        result = speech_recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        else:
            return f"Speech recognition failed: {result.reason}"

    async def text_to_speech(self, text: str):
        speech_config = speechsdk.SpeechConfig(subscription=self.speech_key, region=self.service_region)
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=False)

        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)

        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            audio_stream = io.BytesIO(result.audio_data)
            audio_stream.seek(0)
            return audio_stream
        else:
            raise Exception(f"Text to speech synthesis failed: {result.reason}")
