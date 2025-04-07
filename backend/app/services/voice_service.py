import azure.cognitiveservices.speech as speechsdk
import io
from fastapi import UploadFile

class AzureVoiceService:
    def __init__(self):
        self.speech_key = "YOUR_SPEECH_KEY"
        self.service_region = "YOUR_SERVICE_REGION"

async def stream_speech_to_text(self, callback):
    speech_config = speechsdk.SpeechConfig(subscription=self.speech_key, region=self.service_region)
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    def handle_recognized(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print(f"Recognized: {evt.result.text}")
            callback(evt.result.text)

    speech_recognizer.recognized.connect(handle_recognized)

    speech_recognizer.start_continuous_recognition()


async def stream_text_to_speech(self, text: str, stream_callback):
    speech_config = speechsdk.SpeechConfig(subscription=self.speech_key, region=self.service_region)
    speech_config.speech_synthesis_voice_name = "en-US-JennyMultilingualNeural"
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
    )

    stream = speechsdk.audio.PullAudioOutputStream()
    audio_config = speechsdk.audio.AudioOutputConfig(stream=stream)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    ssml = f"""
    <speak version='1.0' xml:lang='en-US'>
        <voice name='en-US-JennyMultilingualNeural'>
            <prosody rate='medium' pitch='+0st'>
                <mstts:express-as style="chat" styledegree="2.5">
                    {text}
                </mstts:express-as>
            </prosody>
        </voice>
    </speak>
    """

    result = synthesizer.speak_ssml_async(ssml).get()

    buffer = bytearray(4096)
    size = stream.read(buffer)
    while size > 0:
        stream_callback(buffer[:size])
        size = stream.read(buffer)
